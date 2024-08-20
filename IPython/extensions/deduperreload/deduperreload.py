from __future__ import annotations
import ast
import contextlib
import os
import platform
import sys
import textwrap
from types import ModuleType
from typing import TYPE_CHECKING, Any, NamedTuple

from IPython.extensions.deduperreload.deduperreload_patching import (
    DeduperReloaderPatchingMixin,
)

if TYPE_CHECKING:
    TDefinitionAst = ast.FunctionDef | ast.AsyncFunctionDef

DefinitionAst = (ast.FunctionDef, ast.AsyncFunctionDef)


def get_module_file_name(module: ModuleType | str) -> str:
    """Returns the module's file path, or the empty string if it's inaccessible"""
    if (mod := sys.modules.get(module) if isinstance(module, str) else module) is None:
        return ""
    return getattr(mod, "__file__", "") or ""


def compare_ast(node1: ast.AST | list[ast.AST], node2: ast.AST | list[ast.AST]) -> bool:
    """Checks if node1 and node2 have identical AST structure/values, apart from some attributes"""
    if type(node1) is not type(node2):
        return False

    if isinstance(node1, ast.AST):
        for k, v in node1.__dict__.items():
            if k in (
                "lineno",
                "end_lineno",
                "col_offset",
                "end_col_offset",
                "ctx",
                "parent",
            ):
                continue
            if not hasattr(node2, k) or not compare_ast(v, getattr(node2, k)):
                return False
        return True

    elif isinstance(node1, list) and isinstance(node2, list):
        return len(node1) == len(node2) and all(
            compare_ast(n1, n2) for n1, n2 in zip(node1, node2)
        )
    else:
        return node1 == node2


class DependencyNode(NamedTuple):
    """
    Each node represents a function.
    qualified_name: string which represents the namespace/name of the function
    abstract_syntax_tree: subtree of the overall module which corresponds to this function

    qualified_name is of the structure: (namespace1, namespace2, ..., name)

    For example, foo() in the following would be represented as (A, B, foo):

    class A:
        class B:
            def foo():
                pass
    """

    qualified_name: tuple[str, ...]
    abstract_syntax_tree: ast.AST


class AutoreloadTree:
    """
    Recursive data structure to keep track of reloadable functions/methods. Each object corresponds to a specific scope level.
    children: classes inside given scope, maps class name to autoreload tree for that class's scope
    funcs_to_autoreload: list of function names that can be autoreloaded in given scope.
    new_nested_classes: Classes getting added in new autoreload cycle
    """

    def __init__(self) -> None:
        self.children: dict[str, AutoreloadTree] = {}
        self.defs_to_reload: dict[str, ast.AST] = {}
        self.defs_to_delete: set[str] = set()
        self.new_nested_classes: dict[str, ast.AST] = {}

    def traverse_prefixes(self, prefixes: list[str]) -> AutoreloadTree:
        """
        Return ref to the AutoreloadTree at the namespace specified by prefixes
        """
        cur = self
        for prefix in prefixes:
            if prefix not in cur.children:
                cur.children[prefix] = AutoreloadTree()
            cur = cur.children[prefix]
        return cur


class DeduperReloader(DeduperReloaderPatchingMixin):
    """
    This version of autoreload detects when we can leverage targeted recompilation of a subset of a module and patching
    existing function/method objects to reflect these changes.

    Detects what functions/methods can be reloaded by recursively comparing the old/new AST of module-level classes,
    module-level classes' methods, recursing through nested classes' methods. If other changes are made, original
    autoreload algorithm is called directly.
    """

    def __init__(self) -> None:
        self._to_autoreload: AutoreloadTree = AutoreloadTree()
        self.source_by_modname: dict[str, str] = {}
        self.dependency_graph: dict[tuple[str, ...], list[DependencyNode]] = {}
        self._enabled = True
        
    @property
    def enabled(self) -> bool:
        return self._enabled and platform.python_implementation() == "CPython"
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def update_sources(self) -> None:
        """
        Update dictionary source_by_modname with current modules' source codes.
        """
        if not self.enabled:
            return
        for new_modname in sys.modules.keys() - self.source_by_modname.keys():
            new_module = sys.modules[new_modname]
            if (
                (fname := get_module_file_name(new_module)) is None
                or "site-packages" in fname
                or "dist-packages" in fname
                or not os.access(fname, os.R_OK)
            ):
                self.source_by_modname[new_modname] = ""
                continue
            with open(fname, "r") as f:
                try:
                    self.source_by_modname[new_modname] = f.read()
                except Exception:
                    self.source_by_modname[new_modname] = ""

    @classmethod
    def _gather_children(
        cls, body: list[ast.stmt]
    ) -> tuple[dict[str, TDefinitionAst], dict[str, ast.ClassDef], list[ast.AST]]:
        """
        Given list of ast elements, return:
        1. dict mapping function names to their ASTs.
        2. dict mapping class names to their ASTs.
        3. list of any other ASTs.
        """
        defs: dict[str, TDefinitionAst] = {}
        classes: dict[str, ast.ClassDef] = {}
        unfixable: list[ast.AST] = []
        for ast_node in body:
            ast_elt: ast.expr | ast.stmt = ast_node
            if isinstance(ast_node, ast.Expr):
                ast_elt = ast_node.value
            if isinstance(ast_elt, DefinitionAst):
                defs[ast_elt.name] = ast_elt
            elif isinstance(ast_elt, ast.ClassDef):
                classes[ast_elt.name] = ast_elt
            elif isinstance(ast_elt, ast.If):
                unfixable.append(ast_elt.test)
                if_defs, if_classes, if_unfixable = cls._gather_children(ast_elt.body)
                else_defs, else_classes, else_unfixable = cls._gather_children(
                    ast_elt.orelse
                )
                defs.update(if_defs)
                defs.update(else_defs)
                classes.update(if_classes)
                classes.update(else_classes)
                unfixable.extend(if_unfixable)
                unfixable.extend(else_unfixable)
            elif isinstance(ast_elt, (ast.AsyncWith, ast.With)):
                unfixable.extend(ast_elt.items)
                with_defs, with_classes, with_unfixable = cls._gather_children(
                    ast_elt.body
                )
                defs.update(with_defs)
                classes.update(with_classes)
                unfixable.extend(with_unfixable)
            elif isinstance(ast_elt, ast.Try):
                try_defs, try_classes, try_unfixable = cls._gather_children(
                    ast_elt.body
                )
                else_defs, else_classes, else_unfixable = cls._gather_children(
                    ast_elt.orelse
                )
                finally_defs, finally_classes, finally_unfixable = cls._gather_children(
                    ast_elt.finalbody
                )
                defs.update(try_defs)
                defs.update(else_defs)
                defs.update(finally_defs)
                classes.update(try_classes)
                classes.update(else_classes)
                classes.update(finally_classes)
                unfixable.extend(try_unfixable)
                unfixable.extend(else_unfixable)
                unfixable.extend(finally_unfixable)
                for handler in ast_elt.handlers:
                    if handler.type is not None:
                        unfixable.append(handler.type)
                    (
                        handler_defs,
                        handler_classes,
                        handler_unfixable,
                    ) = cls._gather_children(handler.body)
                    defs.update(handler_defs)
                    classes.update(handler_classes)
                    unfixable.extend(handler_unfixable)
            elif not isinstance(ast_elt, (ast.Ellipsis, ast.Pass)):
                unfixable.append(ast_elt)
        return defs, classes, unfixable

    def detect_autoreload(
        self,
        old_node: ast.Module | ast.ClassDef,
        new_node: ast.Module | ast.ClassDef,
        prefixes: list[str] | None = None,
    ) -> bool:
        """
        Returns
        -------
        `True` if we can run our targeted autoreload algorithm safely.
        `False` if we should instead use IPython's original autoreload implementation.
        """
        if not self.enabled:
            return False
        prefixes = prefixes or []

        old_defs, old_classes, old_unfixable = self._gather_children(old_node.body)
        new_defs, new_classes, new_unfixable = self._gather_children(new_node.body)

        if not compare_ast(old_unfixable, new_unfixable):
            return False

        cur = self._to_autoreload.traverse_prefixes(prefixes)
        for name, new_ast_def in new_defs.items():
            if name not in old_defs or not compare_ast(new_ast_def, old_defs[name]):
                cur.defs_to_reload[name] = new_ast_def
        cur.defs_to_delete |= set(old_defs.keys()) - set(new_defs.keys())
        for name, new_ast_def_class in new_classes.items():
            if name not in old_classes:
                cur.new_nested_classes[name] = new_ast_def_class
            elif not compare_ast(
                new_ast_def_class, old_classes[name]
            ) and not self.detect_autoreload(
                old_classes[name], new_ast_def_class, prefixes + [name]
            ):
                return False
        return True

    def _check_dependents(self) -> bool:
        """
        If a decorator function is modified, we should similarly reload the functions which are decorated by this
        decorator. Iterate through the Dependency Graph to find such cases in the given AutoreloadTree.
        """
        for node in self._check_dependents_inner():
            self._add_node_to_autoreload_tree(node)
        return True

    def _add_node_to_autoreload_tree(self, node: DependencyNode) -> None:
        """
        Given a node of the dependency graph, add decorator dependencies to the autoreload tree.
        """
        if len(node.qualified_name) == 0:
            return
        cur = self._to_autoreload.traverse_prefixes(list(node.qualified_name[:-1]))
        if node.abstract_syntax_tree:
            cur.defs_to_reload[node.qualified_name[-1]] = node.abstract_syntax_tree

    def _check_dependents_inner(
        self, prefixes: list[str] | None = None
    ) -> list[DependencyNode]:
        prefixes = prefixes or []
        cur = self._to_autoreload.traverse_prefixes(prefixes)
        ans = []
        for func_name in cur.defs_to_reload:
            node = tuple(prefixes + [func_name])
            ans.extend(self._gen_dependents(node))
        for class_name in cur.new_nested_classes:
            ans.extend(self._check_dependents_inner(prefixes + [class_name]))
        return ans

    def _gen_dependents(self, qualname: tuple[str, ...]) -> list[DependencyNode]:
        ans = []
        if qualname not in self.dependency_graph:
            return []
        for elt in self.dependency_graph[qualname]:
            ans.extend(self._gen_dependents(elt.qualified_name))
            ans.append(elt)
        return ans

    def _patch_namespace_inner(
        self, ns: ModuleType | type, prefixes: list[str] | None = None
    ) -> bool:
        """
        This function patches module functions and methods. Specifically, only objects with their name in
        self.to_autoreload will be considered for patching. If an object has been marked to be autoreloaded,
        new_source_code gets executed in the old version's global environment. Then, replace the old function's
        attributes with the new function's attributes.
        """
        prefixes = prefixes or []
        cur = self._to_autoreload.traverse_prefixes(prefixes)
        namespace_to_check = ns
        for prefix in prefixes:
            namespace_to_check = namespace_to_check.__dict__[prefix]
        for name, new_ast_def in cur.defs_to_reload.items():
            local_env: dict[str, Any] = {}
            if name in namespace_to_check.__dict__:
                to_patch_to = namespace_to_check.__dict__[name]
                if isinstance(to_patch_to, (staticmethod, classmethod)):
                    to_patch_to = to_patch_to.__func__
                # exec new source code using old function's (obj) globals environment.
                func_code = textwrap.dedent(ast.unparse(new_ast_def))
                if is_method := (len(prefixes) > 0):
                    func_code = "class __autoreload_class__:\n" + textwrap.indent(
                        func_code, "    "
                    )
                global_env = namespace_to_check.__dict__
                if hasattr(to_patch_to, "__globals__"):
                    global_env = to_patch_to.__globals__
                elif isinstance(to_patch_to, property):
                    if to_patch_to.fget is not None:
                        global_env = to_patch_to.fget.__globals__
                    elif to_patch_to.fset is not None:
                        global_env = to_patch_to.fset.__globals__
                    elif to_patch_to.fdel is not None:
                        global_env = to_patch_to.fdel.__globals__
                if not isinstance(global_env, dict):
                    global_env = dict(global_env)
                exec(func_code, global_env, local_env)  # type: ignore[arg-type]
                # local_env contains the function exec'd from  new version of function
                if is_method:
                    to_patch_from = getattr(local_env["__autoreload_class__"], name)
                else:
                    to_patch_from = local_env[name]
                if isinstance(to_patch_from, (staticmethod, classmethod)):
                    to_patch_from = to_patch_from.__func__
                if isinstance(to_patch_to, property) and isinstance(
                    to_patch_from, property
                ):
                    for attr in ("fget", "fset", "fdel"):
                        if (
                            getattr(to_patch_to, attr) is None
                            or getattr(to_patch_from, attr) is None
                        ):
                            self.try_patch_attr(to_patch_to, to_patch_from, attr)
                        else:
                            self.patch_function(
                                getattr(to_patch_to, attr),
                                getattr(to_patch_from, attr),
                                is_method,
                            )
                elif not isinstance(to_patch_to, property) and not isinstance(
                    to_patch_from, property
                ):
                    self.patch_function(to_patch_to, to_patch_from, is_method)
                else:
                    raise ValueError(
                        "adding or removing property decorations not supported"
                    )
            else:
                exec(
                    ast.unparse(new_ast_def),
                    ns.__dict__ | namespace_to_check.__dict__,
                    local_env,
                )
                setattr(namespace_to_check, name, local_env[name])
        cur.defs_to_reload.clear()
        for name in cur.defs_to_delete:
            try:
                delattr(namespace_to_check, name)
            except (AttributeError, TypeError, ValueError):
                # give up on deleting the attribute, let the stale one dangle
                pass
        cur.defs_to_delete.clear()
        for class_name, class_ast_node in cur.new_nested_classes.items():
            local_env_class: dict[str, Any] = {}
            exec(
                ast.unparse(class_ast_node),
                ns.__dict__ | namespace_to_check.__dict__,
                local_env_class,
            )
            setattr(namespace_to_check, class_name, local_env_class[class_name])
        cur.new_nested_classes.clear()
        for class_name in cur.children.keys():
            if not self._patch_namespace(ns, prefixes + [class_name]):
                return False
        cur.children.clear()
        return True

    def _patch_namespace(
        self, ns: ModuleType | type, prefixes: list[str] | None = None
    ) -> bool:
        """
        Wrapper for patching all elements in a namespace as specified by the to_autoreload member variable.
        Returns `true` if patching was successful, and `false` if unsuccessful.
        """
        try:
            return self._patch_namespace_inner(ns, prefixes=prefixes)
        except Exception:
            return False

    def maybe_reload_module(self, module: ModuleType) -> bool:
        """
        Uses Deduperreload to try to update a module.
        Returns `true` on success and `false` on failure.
        """
        if not self.enabled:
            return False
        if not (modname := getattr(module, "__name__", None)):
            return False
        if (fname := get_module_file_name(module)) is None:
            return False
        with open(fname, "r") as f:
            new_source_code = f.read()
        patched_flag = False
        if old_source_code := self.source_by_modname.get(modname):
            # get old/new module ast
            try:
                old_module_ast = ast.parse(old_source_code)
                new_module_ast = ast.parse(new_source_code)
            except Exception:
                return False
            # detect if we are able to use our autoreload algorithm
            ctx = contextlib.suppress()
            with ctx:
                self._build_dependency_graph(new_module_ast)
                if (
                    self.detect_autoreload(old_module_ast, new_module_ast)
                    and self._check_dependents()
                    and self._patch_namespace(module)
                ):
                    patched_flag = True

        self.source_by_modname[modname] = new_source_code
        self._to_autoreload = AutoreloadTree()
        return patched_flag

    def _separate_name(
        self,
        decorator: ast.Attribute | ast.Name | ast.Call | ast.expr,
        accept_calls: bool,
    ) -> list[str] | None:
        """
        Generates a qualified name for a given decorator by finding its relative namespace.
        """
        if isinstance(decorator, ast.Name):
            return [decorator.id]
        elif isinstance(decorator, ast.Call):
            if accept_calls:
                return self._separate_name(decorator.func, False)
            else:
                return None
        if not isinstance(decorator, ast.Attribute):
            return None
        if pref := self._separate_name(decorator.value, False):
            return pref + [decorator.attr]
        else:
            return None

    def _gather_dependents(
        self, body: list[ast.stmt], body_prefixes: list[str] | None = None
    ) -> bool:
        body_prefixes = body_prefixes or []
        for ast_node in body:
            ast_elt: ast.expr | ast.stmt = ast_node
            if isinstance(ast_elt, ast.ClassDef):
                self._gather_dependents(ast_elt.body, body_prefixes + [ast_elt.name])
                continue
            if not isinstance(ast_elt, DefinitionAst):
                continue
            qualified_name = tuple(body_prefixes + [ast_elt.name])
            cur_dependency_node = DependencyNode(qualified_name, ast_elt)
            for decorator in ast_elt.decorator_list:
                decorator_path = self._separate_name(decorator, True)
                if not decorator_path:
                    continue
                decorator_path_tuple = tuple(decorator_path)
                self.dependency_graph.setdefault(decorator_path_tuple, []).append(
                    cur_dependency_node
                )
        return True

    def _build_dependency_graph(self, new_ast: ast.Module | ast.ClassDef) -> bool:
        """
        Wrapper function for generating dependency graph given some AST.
        Returns `true` on success. Returns `false` on failure.
        Currently, only returns `true` as we do not block on failure to build this graph.
        """
        return self._gather_dependents(new_ast.body)

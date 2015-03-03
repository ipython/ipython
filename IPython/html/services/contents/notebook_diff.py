'''
    The classes and functions in this file are modified
    versions of code taken from the NBDiff project (nbdiff.org)
'''

import IPython.nbformat as current
from IPython.nbconvert.exporters.html import HTMLExporter
from IPython.nbconvert.preprocessors.base import Preprocessor
import itertools as it
import collections

class NBDiff():
    @staticmethod
    def readnb(json_data):
        data = current.read(json_data, 4)
        json_data.close()
        return data
        
    @staticmethod
    def readjson(json_str):
        data = current.reads(json_str, 4)
        return data
    
    @staticmethod    
    def notebook_diff(nb1, nb2, log, check_modified=True):
        NBDiff.log = log
        nb1_cells = nb1['cells']
        nb2_cells = nb2['cells']

        diffed_nb = NBDiff.cells_diff(nb1_cells, nb2_cells, check_modified=check_modified)
        cell_list = list()
        for i, item in enumerate(diffed_nb):
            cell = NBDiff.diff_result_to_cell(item)
            cell['metadata']['id'] = "cell_" + str(i)
            cell_list.append(cell)
        nb1['cells'] = cell_list
        nb1['metadata']['nbdiff-type'] = 'diff'

        return nb1

    @staticmethod
    def diff_result_to_cell(item):
        state = item['state']
        if state == 'modified':
            new_cell = item['modifiedvalue'].data
            old_cell = item['originalvalue'].data
            old_cell['metadata']['state'] = 'deleted'
            new_cell['metadata']['state'] = 'modified'
            new_cell['metadata']['original'] = old_cell
            new_cell['metadata']['extra-diff-data'] = item['extra_diffs']
            cell = new_cell
        else:
            cell = item['value'].data
            cell['metadata']['state'] = state
        return cell

    @staticmethod
    def cells_diff(before_cells, after_cells, check_modified=False):
        '''Diff two arrays of cells.'''
        before_comps = [
            CellComparator(cell, check_modified=check_modified)
            for cell in before_cells
        ]
        after_comps = [
            CellComparator(cell, check_modified=check_modified)
            for cell in after_cells
        ]
        diff_result = Diff.diff(
            before_comps,
            after_comps,
            check_modified=check_modified
        )
        return diff_result
        
        
class Exporter(HTMLExporter):
    def __init__(self, *args, **kwargs):
        super(Exporter, self).__init__(*args, **kwargs)
        self.register_preprocessor(ExporterPreprocessor, True)
        
    def _template_file_default(self):
        return 'nbdiff'
        
class ExporterPreprocessor(Preprocessor):
    def preprocess(self, nb, resources):
        resources['metadata']['name'] = "Diff"
        return nb, resources
        
class Diff():
    @staticmethod
    def diff(before, after, check_modified=False):
        """Diff two sequences of comparable objects.

        The result of this function is a list of dictionaries containing
        values in ``before`` or ``after`` with a ``state`` of either
        'unchanged', 'added', 'deleted', or 'modified'.

        >>> import pprint
        >>> result = Diff.diff(['a', 'b', 'c'], ['b', 'c', 'd'])
        >>> pprint.pprint(result)
        [{'state': 'deleted', 'value': 'a'},
         {'state': 'unchanged', 'value': 'b'},
         {'state': 'unchanged', 'value': 'c'},
         {'state': 'added', 'value': 'd'}]

        Parameters
        ----------
        before : iterable
            An iterable containing values to be used as the baseline version.
        after : iterable
            An iterable containing values to be compared against the baseline.
        check_modified : bool
            Whether or not to check for modifiedness.

        Returns
        -------
        diff_items : A list of dictionaries containing diff information.
        """

        # The grid will be empty if `before` or `after` are
        # empty; this will violate the assumptions made in the rest
        # of this function.
        # If this is the case, we know what the result of the diff is
        # anyways: the contents of the other, non-empty input.
        if len(before) == 0:
            return [
                {'state': 'added', 'value': v}
                for v in after
            ]
        elif len(after) == 0:
            return [
                {'state': 'deleted', 'value': v}
                for v in before
            ]

        grid = Diff.create_grid(before, after)

        nrows = len(grid[0])
        ncols = len(grid)
        dps = Diff.diff_points(grid)
        result = []
        for kind, col, row, extra_diffs in dps:
            if kind == 'unchanged':
                value = before[col]
                result.append({
                    'state': kind,
                    'value': value,
                })
            elif kind == 'deleted':
                assert col < ncols
                value = before[col]
                result.append({
                    'state': kind,
                    'value': value,
                })
            elif kind == 'added':
                assert row < nrows
                value = after[row]
                result.append({
                    'state': kind,
                    'value': value,
                })
            elif check_modified and kind == 'modified':
                result.append({
                    'state': kind,
                    'originalvalue': before[col],
                    'modifiedvalue': after[row],
                    'extra_diffs': extra_diffs
                })
            elif (not check_modified) and kind == 'modified':
                result.append({
                    'state': 'deleted',
                    'value': before[col],
                })
                result.append({
                    'state': 'added',
                    'value': after[row],
                })
            else:
                raise Exception('We should not be here.')
        return result
    
    @staticmethod
    def diff_points(grid):
        ncols = len(grid)
        nrows = len(grid[0])

        lcs_result = Diff.lcs(grid)
        matched_cols = [r[0] for r in lcs_result]
        matched_rows = [r[1] for r in lcs_result]

        cur_col = 0
        cur_row = 0

        result = []
        while cur_col < ncols or cur_row < nrows:
            passfirst = cur_col < ncols and cur_row < nrows
            goodrow = cur_row < nrows
            goodcol = cur_col < ncols
            if passfirst and lcs_result \
                    and (cur_col, cur_row) == lcs_result[0]:
                lcs_result.pop(0)
                matched_cols.pop(0)
                matched_rows.pop(0)
                comparison = grid[cur_col][cur_row]
                
                if hasattr(comparison, 'is_modified') \
                        and comparison.is_modified():
                    result.append(('modified', cur_col, cur_row, comparison.extra_diffs))
                else:
                    result.append(('unchanged', cur_col, cur_row, None))
                cur_col += 1
                cur_row += 1
            elif goodcol and \
                    (not matched_cols or cur_col != matched_cols[0]):
                assert cur_col < ncols
                result.append(('deleted', cur_col, None, None))
                cur_col += 1
            elif goodrow and \
                    (not matched_rows or cur_row != matched_rows[0]):
                assert cur_row < nrows
                result.append(('added', None, cur_row, None))
                cur_row += 1

        return result

    @staticmethod
    def create_grid(before, after):
        ncols = len(before)
        nrows = len(after)
        all_comps = [b == a for b, a in it.product(before, after)]
        return [
            all_comps[col*(nrows):col*(nrows)+nrows]
            for col in range(ncols)
        ]

    @staticmethod
    def find_matches(col, colNum):
        result = []
        for j in range(len(col)):
            if col[j]:
                result.append((colNum, j))
        return result

    @staticmethod
    def lcs(grid):
        kcs = Diff.find_candidates(grid)
        ks = kcs.keys()
        if len(ks) == 0:
            return []
        highest = max(kcs.keys())
        last_point = kcs[highest][-1]
        cur = highest - 1
        acc = [last_point]
        while cur > 0:
            comp = acc[-1]
            cx, cy = comp
            possibilities = [
                (x, y) for (x, y)
                in reversed(kcs[cur])
                if cx > x and cy > y
            ]
            if len(possibilities) > 0:
                acc.append(possibilities[-1])
            cur -= 1

        return list(reversed(acc))

    @staticmethod
    def process_col(k, col, colNum):
        matches = Diff.find_matches(col, colNum)
        
        d = collections.defaultdict(lambda: [])
        x = 0
        for (i, j) in matches:
            oldx = x
            if not k and not d[1]:
                d[1].append((i, j))
            elif k:
                x = Diff.check_match((i, j), k)
                if x is None:
                    continue
                x = x
                if x == oldx:
                    continue
                d[x].append((i, j))
        return dict(d)

    @staticmethod
    def check_match(point, k):
        result = []
        k_keys = k.keys()
        max_k = max(k_keys)
        new_max_k = max_k + 1
        k_range = list(k_keys) + [new_max_k]
        for x in k_range:
            if x == 1:
                continue

            if point[1] < x-2:
                continue

            above_key = x - 1
            above_x = above_key == new_max_k and \
                10000 or max([l[0] for l in k[above_key]])
            above_y = above_key == new_max_k and \
                10000 or min([l[1] for l in k[above_key]])
            below_key = x - 2
            below_x = below_key < 1 and -1 or max([l[0] for l in k[below_key]])
            below_y = below_key < 1 and -1 or min([l[1] for l in k[below_key]])
            new_x, new_y = point
            if new_x > above_x and new_y < above_y and \
                    new_x > below_x and new_y > below_y:
                result.append(x-1)

        below_key = new_max_k - 1
        below_x = below_key == 0 and -1 or max([l[0] for l in k[new_max_k-1]])
        below_y = below_key == 0 and -1 or min([l[1] for l in k[new_max_k-1]])
        new_x, new_y = point
        if new_x > below_x and new_y > below_y:
            result.append(new_max_k)
        if len(result) > 0:
            actual_result = result[0]
            # print result
            assert point[1] >= actual_result-1
            return (result)[0]
        else:
            return None

    @staticmethod
    def add_results(k, result):
        finalResult = collections.defaultdict(lambda: [], k)
        for x in result.keys():
            finalResult[x] = finalResult[x] + result[x]
        return finalResult

    @staticmethod
    def find_candidates(grid):
        k = collections.defaultdict(lambda: [])
        for colNum in range(len(grid)):
            k = Diff.add_results(k, Diff.process_col(k, grid[colNum], colNum))
        return dict(k)
        
    @staticmethod
    def similarity_ratio(diff):
        modified = 0.0
        unchanged = 0.0
        for dict in diff:
            if dict['state'] == "added" or dict['state'] == "deleted":
                modified += 1
            elif dict['state'] == "unchanged":
                unchanged += 1
        if modified == 0 and unchanged == 0:
            unchanged = 1
        return unchanged/(modified + unchanged)
        

class BooleanPlus(object):
    def __init__(self, truthfulness, mod, extra_diffs=None):
        self.truth = truthfulness
        self.modified = mod
        self.extra_diffs = extra_diffs

    def __bool__(self):
        ''' for evaluating as a boolean '''
        return self.truth
        
    def __nonzero__(self):
        """ Python 2 compatibility """
        return self.__bool__

    def is_modified(self):
        return self.modified


class CellComparator():
    def __init__(self, data, check_modified=False):
        self.data = data
        self.check_modified = check_modified

    def __eq__(self, other):
        return self.equal(self.data, other.data)

    def equal(self, cell1, cell2):
        if not cell1["cell_type"] == cell2["cell_type"]:
            return False
        if cell1["cell_type"] == "code":
            return self.compare_code_cells(cell1, cell2)
        return self.compare_source_cells(cell1, cell2)
            
    def compare_source_cells(self, cell1, cell2):
        if cell1['source'] == cell2['source']:
            return True
        if not self.check_modified:
            return False
        result = Diff.diff(
            cell1["source"].splitlines(),
            cell2["source"].splitlines()
        )
        ''' if input is 2 or less lines of code compare by terms instead '''
        input = list()
        if len(cell1["source"].splitlines()) < 4:
            input = Diff.diff(
                cell1["source"].split(" "),
                cell2["source"].split(" ")
            )
        else:
            input = result
        modifiedness = Diff.similarity_ratio(input)
        if modifiedness >= 0.6:
            return BooleanPlus(True, True, {'source':result})
        else:
            return False

    def equaloutputs(self, output1, output2):
        if not len(output1) == len(output2):
            return False
        for i in range(0, len(output1)):
            if not CellOutputComparator(output1[i]) == CellOutputComparator(output2[i]):
                return False
        return True

    def compare_code_cells(self, cell1, cell2):
        '''
        return true if exactly equal or if equal but modified,
        otherwise return false
        return type: BooleanPlus
        '''
        eqinput = cell1["source"] == cell2["source"]
        eqoutputs = self.equaloutputs(cell1["outputs"], cell2["outputs"])

        if eqinput and eqoutputs:
            return BooleanPlus(True, False)
        elif not self.check_modified:
            return BooleanPlus(False, False)
        
        source = Diff.diff(
            cell1["source"].splitlines(),
            cell2["source"].splitlines()
        )
        
        ''' if input is 3 or less lines of code compare by words instead '''
        input = list()
        if len(cell1["source"].splitlines()) < 4:
            input = Diff.diff(
                cell1["source"].split(" "),
                cell2["source"].split(" ")
            )
        else:
            input = source
        
        outputs = Diff.diff(
            [CellOutputComparator(out) for out in cell1["outputs"]],
            [CellOutputComparator(out) for out in cell2["outputs"]]
        )
        for output in outputs:
            output['value'] = output['value'].data
        similarity_percent = Diff.similarity_ratio(input)
        if similarity_percent >= 0.6:
            return BooleanPlus(True, True, {'source':source, 'outputs':outputs})
        return BooleanPlus(False, False)

        
class CellOutputComparator():
    def __init__(self, data):
        self.data = data

    def __eq__(self, other):
        return self.equal(self.data, other.data)

    def equal(self, output1, output2):
        if output1['output_type'] != output2['output_type']:
            return False
        if 'data' in output1 and 'data' in output2:
            if 'image/png' in output1['data'] and 'image/png' in output2['data']:
                return output1['data']['image/png'] == output2['data']['image/png']
            return output1['data'] == output2['data']
        return output1 == output2

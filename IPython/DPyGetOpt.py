# -*- coding: utf-8 -*-
"""DPyGetOpt -- Demiurge Python GetOptions Module

 $Id: DPyGetOpt.py 2872 2007-11-25 17:58:05Z fperez $

This module is modeled after perl's Getopt::Long module-- which
is, in turn, modeled after GNU's extended getopt() function.

Upon instantiation, the option specification should be a sequence
(list) of option definitions.

Options that take no arguments should simply contain the name of
the option.  If a ! is post-pended, the option can be negated by
prepending 'no';  ie 'debug!' specifies that -debug and -nodebug
should be accepted.

Mandatory arguments to options are specified using a postpended
'=' + a type specifier.  '=s' specifies a mandatory string
argument, '=i' specifies a mandatory integer argument, and '=f'
specifies a mandatory real number.  In all cases, the '=' can be
substituted with ':' to specify that the argument is optional.

Dashes '-' in option names are allowed.

If an option has the character '@' postpended (after the
argumentation specification), it can appear multiple times within
each argument list that is processed. The results will be stored
in a list.

The option name can actually be a list of names separated by '|'
characters;  ie-- 'foo|bar|baz=f@' specifies that all -foo, -bar,
and -baz options that appear on within the parsed argument list
must have a real number argument and that the accumulated list
of values will be available under the name 'foo'

$Id: DPyGetOpt.py 2872 2007-11-25 17:58:05Z fperez $"""

#*****************************************************************************
#
# Copyright (c) 2001 Bill Bumgarner <bbum@friday.com>
#
#
# Published under the terms of the MIT license, hereby reproduced:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
#*****************************************************************************

__author__  = 'Bill Bumgarner <bbum@friday.com>'
__license__ = 'MIT'
__version__ = '1.2'

# Modified to use re instead of regex and regsub modules.
# 2001/5/7, Jonathan Hogg <jonathan@onegoodidea.com>

import re
import string
import sys
import types

class Error(Exception):
    """Base class for exceptions in the DPyGetOpt module."""

class ArgumentError(Error):
    """Exception indicating an error in the arguments passed to
    DPyGetOpt.processArguments."""

class SpecificationError(Error):
    """Exception indicating an error with an option specification."""

class TerminationError(Error):
    """Exception indicating an error with an option processing terminator."""

specificationExpr = re.compile('(?P<required>.)(?P<type>.)(?P<multi>@?)')

ArgRequired     = 'Requires an Argument'
ArgOptional     = 'Argument Optional'

# The types modules is not used for these identifiers because there
# is no identifier for 'boolean' or 'generic'
StringArgType   = 'String Argument Type'
IntegerArgType  = 'Integer Argument Type'
RealArgType             = 'Real Argument Type'
BooleanArgType  = 'Boolean Argument Type'
GenericArgType  = 'Generic Argument Type'

# dictionary of conversion functions-- boolean and generic options
# do not accept arguments and do not need conversion functions;
# the identity function is used purely for convenience.
ConversionFunctions = {
        StringArgType : lambda x: x,
        IntegerArgType : string.atoi,
        RealArgType : string.atof,
        BooleanArgType : lambda x: x,
        GenericArgType : lambda x: x,
        }

class DPyGetOpt:

    def __init__(self, spec = None, terminators = ['--']):
        """
        Declare and intialize instance variables

        Yes, declaration is not necessary... but one of the things
        I sorely miss from C/Obj-C is the concept of having an
        interface definition that clearly declares all instance
        variables and methods without providing any implementation
         details.   it is a useful reference!

        all instance variables are initialized to 0/Null/None of
        the appropriate type-- not even the default value...
        """

#               sys.stderr.write(string.join(spec) + "\n")

        self.allowAbbreviations = 1  # boolean, 1 if abbreviations will
                                                                                  # be expanded
        self.freeValues         = [] # list, contains free values
        self.ignoreCase         = 0  # boolean, YES if ignoring case
        self.needsParse         = 0  # boolean, YES if need to reparse parameter spec
        self.optionNames        = {} # dict, all option names-- value is index of tuple
        self.optionStartExpr    = None # regexp defining the start of an option (ie; '-', '--')
        self.optionTuples       = [] # list o' tuples containing defn of options AND aliases
        self.optionValues       = {} # dict, option names (after alias expansion) -> option value(s)
        self.orderMixed         = 0  # boolean, YES if options can be mixed with args
        self.posixCompliance    = 0  # boolean, YES indicates posix like behaviour
        self.spec               = [] # list, raw specs (in case it must be reparsed)
        self.terminators        = terminators # list, strings that terminate argument processing
        self.termValues         = [] # list, values after terminator
        self.terminator         = None # full name of terminator that ended
                                               # option processing

        # set up defaults
        self.setPosixCompliance()
        self.setIgnoreCase()
        self.setAllowAbbreviations()

        # parse spec-- if present
        if spec:
            self.parseConfiguration(spec)

    def setPosixCompliance(self, aFlag = 0):
        """
        Enables and disables posix compliance.

        When enabled, '+' can be used as an option prefix and free
        values can be mixed with options.
        """
        self.posixCompliance = aFlag
        self.needsParse = 1

        if self.posixCompliance:
            self.optionStartExpr = re.compile('(--|-)(?P<option>[A-Za-z0-9_-]+)(?P<arg>=.*)?')
            self.orderMixed = 0
        else:
            self.optionStartExpr = re.compile('(--|-|\+)(?P<option>[A-Za-z0-9_-]+)(?P<arg>=.*)?')
            self.orderMixed = 1

    def isPosixCompliant(self):
        """
        Returns the value of the posix compliance flag.
        """
        return self.posixCompliance

    def setIgnoreCase(self, aFlag = 1):
        """
        Enables and disables ignoring case during option processing.
        """
        self.needsParse = 1
        self.ignoreCase = aFlag

    def ignoreCase(self):
        """
        Returns 1 if the option processor will ignore case when
        processing options.
        """
        return self.ignoreCase

    def setAllowAbbreviations(self, aFlag = 1):
        """
        Enables and disables the expansion of abbreviations during
        option processing.
        """
        self.allowAbbreviations = aFlag

    def willAllowAbbreviations(self):
        """
        Returns 1 if abbreviated options will be automatically
        expanded to the non-abbreviated form (instead of causing an
        unrecognized option error).
        """
        return self.allowAbbreviations

    def addTerminator(self, newTerm):
        """
        Adds newTerm as terminator of option processing.

        Whenever the option processor encounters one of the terminators
        during option processing, the processing of options terminates
        immediately, all remaining options are stored in the termValues
        instance variable and the full name of the terminator is stored
        in the terminator instance variable.
        """
        self.terminators = self.terminators + [newTerm]

    def _addOption(self, oTuple):
        """
        Adds the option described by oTuple (name, (type, mode,
        default), alias) to optionTuples.  Adds index keyed under name
        to optionNames.  Raises SpecificationError if name already in
        optionNames
        """
        (name, (type, mode, default, multi), realName) = oTuple

        # verify name and add to option names dictionary
        if self.optionNames.has_key(name):
            if realName:
                raise SpecificationError('Alias \'' + name + '\' for \'' +
                                         realName +
                                         '\' already used for another option or alias.')
            else:
                raise SpecificationError('Option named \'' + name +
                                         '\' specified more than once. Specification: '
                                         + option)

        # validated. add to optionNames
        self.optionNames[name] = self.tupleIndex
        self.tupleIndex = self.tupleIndex + 1

        # add to optionTuples
        self.optionTuples = self.optionTuples + [oTuple]

        # if type is boolean, add negation
        if type == BooleanArgType:
            alias            = 'no' + name
            specTuple = (type, mode, 0, multi)
            oTuple = (alias, specTuple, name)

            # verify name and add to option names dictionary
            if self.optionNames.has_key(alias):
                if realName:
                    raise SpecificationError('Negated alias \'' + name +
                                             '\' for \'' + realName +
                                             '\' already used for another option or alias.')
                else:
                    raise SpecificationError('Negated option named \'' + name +
                                             '\' specified more than once. Specification: '
                                             + option)

            # validated. add to optionNames
            self.optionNames[alias] = self.tupleIndex
            self.tupleIndex = self.tupleIndex + 1

            # add to optionTuples
            self.optionTuples = self.optionTuples + [oTuple]

    def addOptionConfigurationTuple(self, oTuple):
        (name, argSpec, realName) = oTuple
        if self.ignoreCase:
            name = string.lower(name)
            if realName:
                realName = string.lower(realName)
            else:
                realName = name

            oTuple = (name, argSpec, realName)

        # add option
        self._addOption(oTuple)

    def addOptionConfigurationTuples(self, oTuple):
        if type(oTuple) is ListType:
            for t in oTuple:
                self.addOptionConfigurationTuple(t)
        else:
            self.addOptionConfigurationTuple(oTuple)

    def parseConfiguration(self, spec):
        # destroy previous stored information + store raw spec
        self.spec                       = spec
        self.optionTuples       = []
        self.optionNames  = {}
        self.tupleIndex   = 0

        tupleIndex = 0

        # create some regex's for parsing each spec
        splitExpr = \
                                 re.compile('(?P<names>\w+[-A-Za-z0-9|]*)?(?P<spec>!|[=:][infs]@?)?')
        for option in spec:
 # push to lower case (does not negatively affect
 # specification)
            if self.ignoreCase:
                option = string.lower(option)

            # break into names, specification
            match = splitExpr.match(option)
            if match is None:
                raise SpecificationError('Invalid specification {' + option +
                                         '}')

            names                     = match.group('names')
            specification = match.group('spec')

            # break name into name, aliases
            nlist = string.split(names, '|')

            # get name
            name      = nlist[0]
            aliases = nlist[1:]

            # specificationExpr = regex.symcomp('\(<required>.\)\(<type>.\)\(<multi>@?\)')
            if not specification:
                #spec tuple is ('type', 'arg mode', 'default value', 'multiple')
                argType         = GenericArgType
                argMode         = None
                argDefault      = 1
                argMultiple     = 0
            elif specification == '!':
                argType         = BooleanArgType
                argMode         = None
                argDefault      = 1
                argMultiple     = 0
            else:
                # parse
                match = specificationExpr.match(specification)
                if match is None:
                    # failed to parse, die
                    raise SpecificationError('Invalid configuration for option \''
                                             + option + '\'')

                # determine mode
                required = match.group('required')
                if required == '=':
                    argMode = ArgRequired
                elif required == ':':
                    argMode = ArgOptional
                else:
                    raise SpecificationError('Unknown requirement configuration \''
                                             + required + '\'')

                # determine type
                type = match.group('type')
                if type == 's':
                    argType   = StringArgType
                    argDefault = ''
                elif type == 'i':
                    argType   = IntegerArgType
                    argDefault = 1
                elif type == 'f' or type == 'n':
                    argType   = RealArgType
                    argDefault = 1
                else:
                    raise SpecificationError('Unknown type specifier \'' +
                                             type + '\'')

                # determine quantity
                if match.group('multi') == '@':
                    argMultiple = 1
                else:
                    argMultiple = 0
            ## end else (of not specification)

            # construct specification tuple
            specTuple = (argType, argMode, argDefault, argMultiple)

            # add the option-- option tuple is (name, specTuple, real name)
            oTuple = (name, specTuple, name)
            self._addOption(oTuple)

            for alias in aliases:
                # drop to all lower (if configured to do so)
                if self.ignoreCase:
                    alias = string.lower(alias)
                # create configuration tuple
                oTuple = (alias, specTuple, name)
                # add
                self._addOption(oTuple)

        # successfully parsed....
        self.needsParse = 0

    def _getArgTuple(self, argName):
        """
        Returns a list containing all the specification tuples that
        match argName.  If none match, None is returned.  If one
        matches, a list with one tuple is returned.  If more than one
        match, a list containing all the tuples that matched is
        returned.

        In other words, this function does not pass judgement upon the
        validity of multiple matches.
        """
        # is it in the optionNames dict?

        try:
#                       sys.stderr.write(argName + string.join(self.optionNames.keys()) + "\n")

            # yes, get index
            tupleIndex = self.optionNames[argName]
            # and return tuple as element of list
            return [self.optionTuples[tupleIndex]]
        except KeyError:
            # are abbreviations allowed?
            if not self.allowAbbreviations:
                # No! terefore, this cannot be valid argument-- nothing found
                return None

        # argName might be an abbreviation (and, abbreviations must
        # be allowed... or this would not have been reached!)

        # create regex for argName
        argExpr = re.compile('^' + argName)

        tuples = filter(lambda x, argExpr=argExpr: argExpr.search(x[0]) is not None,
                                                  self.optionTuples)

        if not len(tuples):
            return None
        else:
            return tuples

    def _isTerminator(self, optionName):
        """
        Returns the full name of the terminator if optionName is a valid
        terminator.  If it is, sets self.terminator to the full name of
        the terminator.

        If more than one terminator matched, raises a TerminationError with a
        string describing the ambiguity.
        """

#               sys.stderr.write(optionName + "\n")
#               sys.stderr.write(repr(self.terminators))

        if optionName in self.terminators:
            self.terminator = optionName
        elif not self.allowAbbreviations:
            return None

# regex thing in bogus
#               termExpr = regex.compile('^' + optionName)

        terms = filter(lambda x, on=optionName: string.find(x,on) == 0, self.terminators)

        if not len(terms):
            return None
        elif len(terms) > 1:
            raise TerminationError('Ambiguous terminator \'' + optionName +
                                   '\' matches ' + repr(terms))

        self.terminator = terms[0]
        return self.terminator

    def processArguments(self, args = None):
        """
        Processes args, a list of arguments (including options).

        If args is the same as sys.argv, automatically trims the first
        argument (the executable name/path).

        If an exception is not raised, the argument list was parsed
        correctly.

        Upon successful completion, the freeValues instance variable
        will contain all the arguments that were not associated with an
        option in the order they were encountered.  optionValues is a
        dictionary containing the value of each option-- the method
        valueForOption() can be used to query this dictionary.
        terminator will contain the argument encountered that terminated
        option processing (or None, if a terminator was never
        encountered) and termValues will contain all of the options that
        appeared after the Terminator (or an empty list).
        """

        if hasattr(sys, "argv") and args == sys.argv:
            args = sys.argv[1:]

        max             = len(args) # maximum index + 1
        self.freeValues = []        # array to hold return values
        self.optionValues= {}
        index           = 0         # initial index
        self.terminator = None
        self.termValues  = []

        while index < max:
            # obtain argument
            arg = args[index]
            # increment index -- REMEMBER; it is NOW incremented
            index = index + 1

            # terminate immediately if option terminator encountered
            if self._isTerminator(arg):
                self.freeValues = self.freeValues + args[index:]
                self.termValues = args[index:]
                return

            # is this possibly an option?
            match = self.optionStartExpr.match(arg)
            if match is None:
                # not an option-- add to freeValues
                self.freeValues = self.freeValues + [arg]
                if not self.orderMixed:
                    # mixing not allowed;  add rest of args as freeValues
                    self.freeValues = self.freeValues + args[index:]
                    # return to caller
                    return
                else:
                    continue

            # grab name
            optName = match.group('option')

            # obtain next argument-- index has already been incremented
            nextArg = match.group('arg')
            if nextArg:
                nextArg = nextArg[1:]
                index = index - 1 # put it back
            else:
                try:
                    nextArg = args[index]
                except:
                    nextArg = None

            # transpose to lower case, if necessary
            if self.ignoreCase:
                optName = string.lower(optName)

            # obtain defining tuple
            tuples = self._getArgTuple(optName)

            if tuples == None:
                raise ArgumentError('Illegal option \'' + arg + '\'')
            elif len(tuples) > 1:
                raise ArgumentError('Ambiguous option \'' + arg +
                                    '\';  matches ' +
                                    repr(map(lambda x: x[0], tuples)))
            else:
                config = tuples[0]

            # config is now set to the configuration tuple for the
            # argument
            (fullName, spec, realName) = config
            (optType, optMode, optDefault, optMultiple) = spec

            # if opt mode required, but nextArg is none, raise an error
            if (optMode == ArgRequired):
                if (not nextArg) or self._isTerminator(nextArg):
#                                       print nextArg
                    raise ArgumentError('Option \'' + arg +
                                        '\' requires an argument of type ' +
                                        optType)

            if (not optMode == None) and nextArg and (not self._isTerminator(nextArg)):
                # nextArg defined, option configured to possibly consume arg
                try:
                    # grab conversion function-- the try is more for internal diagnostics
                    func = ConversionFunctions[optType]
                    try:
                        optionValue = func(nextArg)
                        index = index + 1
                    except:
                        # only raise conversion error if REQUIRED to consume argument
                        if optMode == ArgRequired:
                            raise ArgumentError('Invalid argument to option \''
                                                + arg + '\';  should be \'' +
                                                optType + '\'')
                        else:
                            optionValue = optDefault
                except ArgumentError:
                    raise
                except:
                    raise ArgumentError('(' + arg +
                                        ') Conversion function for \'' +
                                        optType + '\' not found.')
            else:
                optionValue = optDefault

            # add value to options dictionary
            if optMultiple:
                # can be multiple values
                try:
                    # try to append element
                    self.optionValues[realName] = self.optionValues[realName] + [optionValue]
                except:
                    # failed-- must not exist;  add it
                    self.optionValues[realName] = [optionValue]
            else:
                # only one value per
                if self.isPosixCompliant and self.optionValues.has_key(realName):
                    raise ArgumentError('Argument \'' + arg +
                                        '\' occurs multiple times.')

                self.optionValues[realName] = optionValue

    def valueForOption(self, optionName, defaultValue = None):
        """
        Return the value associated with optionName.  If optionName was
        not encountered during parsing of the arguments, returns the
        defaultValue (which defaults to None).
        """
        try:
            optionValue = self.optionValues[optionName]
        except:
            optionValue = defaultValue

        return optionValue

##
## test/example section
##
test_error = 'Test Run Amok!'
def _test():
    """
    A relatively complete test suite.
    """
    try:
        DPyGetOpt(['foo', 'bar=s', 'foo'])
    except Error, exc:
        print 'EXCEPTION (should be \'foo\' already used..): %s' % exc

    try:
        DPyGetOpt(['foo|bar|apple=s@', 'baz|apple!'])
    except Error, exc:
        print 'EXCEPTION (should be duplicate alias/name error): %s' % exc

    x = DPyGetOpt(['apple|atlas=i@', 'application|executable=f@'])
    try:
        x.processArguments(['-app', '29.3'])
    except Error, exc:
        print 'EXCEPTION (should be ambiguous argument): %s' % exc

    x = DPyGetOpt(['foo'], ['antigravity', 'antithesis'])
    try:
        x.processArguments(['-foo', 'anti'])
    except Error, exc:
        print 'EXCEPTION (should be ambiguous terminator): %s' % exc

    profile = ['plain-option',
                              'boolean-option!',
                              'list-of-integers=i@',
                              'list-real-option|list-real-alias|list-real-pseudonym=f@',
                              'optional-string-option:s',
                              'abbreviated-string-list=s@']

    terminators = ['terminator']

    args = ['-plain-option',
                      '+noboolean-option',
                      '--list-of-integers', '1',
                      '+list-of-integers', '2',
                      '-list-of-integers', '3',
                      'freeargone',
                      '-list-real-option', '1.1',
                      '+list-real-alias', '1.2',
                      '--list-real-pseudonym', '1.3',
                      'freeargtwo',
                      '-abbreviated-string-list', 'String1',
                      '--abbreviated-s', 'String2',
                      '-abbrev', 'String3',
                      '-a', 'String4',
                      '-optional-string-option',
                      'term',
                      'next option should look like an invalid arg',
                      '-a']


    print 'Using profile: ' + repr(profile)
    print 'With terminator: ' + repr(terminators)
    print 'Processing arguments: ' + repr(args)

    go = DPyGetOpt(profile, terminators)
    go.processArguments(args)

    print 'Options (and values): ' + repr(go.optionValues)
    print 'free args: ' + repr(go.freeValues)
    print 'term args: ' + repr(go.termValues)

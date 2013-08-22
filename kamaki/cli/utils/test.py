# Copyright 2013 GRNET S.A. All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
#   1. Redistributions of source code must retain the above
#      copyright notice, this list of conditions and the following
#      disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY GRNET S.A. ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL GRNET S.A OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be
# interpreted as representing official policies, either expressed
# or implied, of GRNET S.A.

from unittest import TestCase
from tempfile import NamedTemporaryFile
from mock import patch, call
from itertools import product


class UtilsMethods(TestCase):

    def assert_dicts_are_equal(self, d1, d2):
        for k, v in d1.items():
            self.assertTrue(k in d2)
            if isinstance(v, dict):
                self.assert_dicts_are_equal(v, d2[k])
            else:
                self.assertEqual(unicode(v), unicode(d2[k]))

    def test_guess_mime_type(self):
        from kamaki.cli.utils import guess_mime_type
        from mimetypes import guess_type
        for args in product(
                ('file.txt', 'file.png', 'file.zip', 'file.gz', None, 'X'),
                ('a type', None),
                ('an/encoding', None)):
            filename, ctype, cencoding = args
            if filename:
                exp_type, exp_enc = guess_type(filename)
                self.assertEqual(
                    guess_mime_type(*args),
                    (exp_type or ctype, exp_enc or cencoding))
            else:
                self.assertRaises(AssertionError, guess_mime_type, *args)

    @patch('kamaki.cli.utils.dumps', return_value='(dumps output)')
    @patch('kamaki.cli.utils._print')
    def test_print_json(self, PR, JD):
        from kamaki.cli.utils import print_json, INDENT_TAB
        print_json('some data')
        JD.assert_called_once_with('some data', indent=INDENT_TAB)
        PR.assert_called_once_with('(dumps output)')

    @patch('kamaki.cli.utils._print')
    def test_print_dict(self, PR):
        from kamaki.cli.utils import print_dict, INDENT_TAB
        call_counter = 0
        self.assertRaises(AssertionError, print_dict, 'non-dict think')
        self.assertRaises(AssertionError, print_dict, {}, indent=-10)
        for args in product(
                (
                    {'k1': 'v1'},
                    {'k1': 'v1', 'k2': 'v2'},
                    {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'},
                    {'k1': 'v1', 'k2': {'k1': 'v1', 'k2': 'v2'}, 'k3': 'v3'},
                    {
                        'k1': {'k1': 'v1', 'k2': 'v2'},
                        'k2': [1, 2, 3],
                        'k3': 'v3'},
                    {
                        'k1': {'k1': 'v1', 'k2': 'v2'},
                        'k2': 42,
                        'k3': {'k1': 1, 'k2': [1, 2, 3]}},
                    {
                        'k1': {
                            'k1': 'v1',
                            'k2': [1, 2, 3],
                            'k3': {'k1': [(1, 2)]}},
                        'k2': (3, 4, 5),
                        'k3': {'k1': 1, 'k2': [1, 2, 3]}}),
                (tuple(), ('k1', ), ('k1', 'k2')),
                (0, 1, 2, 9), (False, True), (False, True)):
            d, exclude, indent, with_enumeration, recursive_enumeration = args
            with patch('kamaki.cli.utils.print_dict') as PD:
                with patch('kamaki.cli.utils.print_list') as PL:
                    pd_calls, pl_calls = 0, 0
                    print_dict(*args)
                    exp_calls = []
                    for i, (k, v) in enumerate(d.items()):
                        if k in exclude:
                            continue
                        str_k = ' ' * indent
                        str_k += '%s.' % (i + 1) if with_enumeration else ''
                        str_k += '%s:' % k
                        if isinstance(v, dict):
                            self.assertEqual(
                                PD.mock_calls[pd_calls],
                                call(
                                    v,
                                    exclude,
                                    indent + INDENT_TAB,
                                    recursive_enumeration,
                                    recursive_enumeration))
                            pd_calls += 1
                            exp_calls.append(call(str_k))
                        elif isinstance(v, list) or isinstance(v, tuple):
                            self.assertEqual(
                                PL.mock_calls[pl_calls],
                                call(
                                    v,
                                    exclude,
                                    indent + INDENT_TAB,
                                    recursive_enumeration,
                                    recursive_enumeration))
                            pl_calls += 1
                            exp_calls.append(call(str_k))
                        else:
                            exp_calls.append(call('%s %s' % (str_k, v)))
                    real_calls = PR.mock_calls[call_counter:]
                    call_counter = len(PR.mock_calls)
                    self.assertEqual(sorted(real_calls), sorted(exp_calls))

    @patch('kamaki.cli.utils._print')
    def test_print_list(self, PR):
        from kamaki.cli.utils import print_list, INDENT_TAB
        call_counter = 0
        self.assertRaises(AssertionError, print_list, 'non-list non-tuple')
        self.assertRaises(AssertionError, print_list, {}, indent=-10)
        for args in product(
                (
                    ['v1', ],
                    ('v2', 'v3'),
                    [1, '2', 'v3'],
                    ({'k1': 'v1'}, 2, 'v3'),
                    [(1, 2), 'v2', [(3, 4), {'k3': [5, 6], 'k4': 7}]]),
                (tuple(), ('v1', ), ('v1', 1), ('v1', 'k3')),
                (0, 1, 2, 9), (False, True), (False, True)):
            l, exclude, indent, with_enumeration, recursive_enumeration = args
            with patch('kamaki.cli.utils.print_dict') as PD:
                with patch('kamaki.cli.utils.print_list') as PL:
                    pd_calls, pl_calls = 0, 0
                    print_list(*args)
                    exp_calls = []
                    for i, v in enumerate(l):
                        str_v = ' ' * indent
                        str_v += '%s.' % (i + 1) if with_enumeration else ''
                        if isinstance(v, dict):
                            if with_enumeration:
                                exp_calls.append(call(str_v))
                            elif i and i < len(l):
                                exp_calls.append(call())
                            self.assertEqual(
                                PD.mock_calls[pd_calls],
                                call(
                                    v,
                                    exclude,
                                    indent + (
                                        INDENT_TAB if with_enumeration else 0),
                                    recursive_enumeration,
                                    recursive_enumeration))
                            pd_calls += 1
                        elif isinstance(v, list) or isinstance(v, tuple):
                            if with_enumeration:
                                exp_calls.append(call(str_v))
                            elif i and i < len(l):
                                exp_calls.append(call())
                            self.assertEqual(
                                PL.mock_calls[pl_calls],
                                call(
                                    v,
                                    exclude,
                                    indent + INDENT_TAB,
                                    recursive_enumeration,
                                    recursive_enumeration))
                            pl_calls += 1
                        elif ('%s' % v) in exclude:
                            continue
                        else:
                            exp_calls.append(call('%s%s' % (str_v, v)))
                    real_calls = PR.mock_calls[call_counter:]
                    call_counter = len(PR.mock_calls)
                    self.assertEqual(sorted(real_calls), sorted(exp_calls))

    @patch('__builtin__.raw_input')
    def test_page_hold(self, RI):
        from kamaki.cli.utils import page_hold
        ri_counter = 0
        for args, expected in (
                ((0, 0, 0), False),
                ((1, 3, 10), True),
                ((3, 3, 10), True),
                ((5, 3, 10), True),
                ((6, 3, 10), True),
                ((10, 3, 10), False),
                ((11, 3, 10), False)):
            self.assertEqual(page_hold(*args), expected)
            index, limit, maxlen = args
            if index and index < maxlen and index % limit == 0:
                self.assertEqual(ri_counter + 1, len(RI.mock_calls))
                self.assertEqual(RI.mock_calls[-1], call(
                    '(%s listed - %s more - "enter" to continue)' % (
                        index, maxlen - index)))
            else:
                self.assertEqual(ri_counter, len(RI.mock_calls))
            ri_counter = len(RI.mock_calls)

    @patch('kamaki.cli.utils._print')
    @patch('kamaki.cli.utils._write')
    @patch('kamaki.cli.utils.print_dict')
    @patch('kamaki.cli.utils.print_list')
    @patch('kamaki.cli.utils.page_hold')
    @patch('kamaki.cli.utils.bold', return_value='bold')
    def test_print_items(self, bold, PH, PL, PD, WR, PR):
        from kamaki.cli.utils import print_items, INDENT_TAB
        for args in product(
                (
                    42, None, 'simple outputs',
                    [1, 2, 3], {1: 1, 2: 2}, (3, 4),
                    ({'k': 1, 'id': 2}, [5, 6, 7], (8, 9), '10')),
                (('id', 'name'), ('something', 2), ('lala', )),
                (False, True),
                (False, True),
                (0, 1, 2, 10)):
            items, title, with_enumeration, with_redundancy, page_size = args
            wr_counter, pr_counter = len(WR.mock_calls), len(PR.mock_calls)
            pl_counter, pd_counter = len(PL.mock_calls), len(PD.mock_calls)
            bold_counter, ph_counter = len(bold.mock_calls), len(PH.mock_calls)
            print_items(*args)
            if not (isinstance(items, dict) or isinstance(
                    items, list) or isinstance(items, tuple)):
                if items:
                    self.assertEqual(PR.mock_calls[-1], call('%s' % items))
            else:
                for i, item in enumerate(items):
                    if with_enumeration:
                        self.assertEqual(
                            WR.mock_calls[wr_counter],
                            call('%s. ' % (i + 1)))
                        wr_counter += 1
                    if isinstance(item, dict):
                        title = sorted(set(title).intersection(item))
                        pick = item.get if with_redundancy else item.pop
                        header = ' '.join('%s' % pick(key) for key in title)
                        self.assertEqual(
                            bold.mock_calls[bold_counter], call(header))
                        self.assertEqual(
                            PR.mock_calls[pr_counter], call('bold'))
                        self.assertEqual(
                            PD.mock_calls[pd_counter],
                            call(item, indent=INDENT_TAB))
                        pr_counter += 1
                        pd_counter += 1
                        bold_counter += 1
                    elif isinstance(item, list) or isinstance(item, tuple):
                        self.assertEqual(
                            PL.mock_calls[pl_counter],
                            call(item, indent=INDENT_TAB))
                        pl_counter += 1
                    else:
                        self.assertEqual(
                            PR.mock_calls[pr_counter], call(' %s' % item))
                        pr_counter += 1
                    page_size = page_size if page_size > 0 else len(items)
                    self.assertEqual(
                        PH.mock_calls[ph_counter],
                        call(i + 1, page_size, len(items)))
                    ph_counter += 1

    def test_format_size(self):
        from kamaki.cli.utils import format_size
        from kamaki.cli import CLIError
        for v in ('wrong', {1: '1', 2: '2'}, ('tuples', 'not OK'), [1, 2]):
            self.assertRaises(CLIError, format_size, v)
        for step, B, K, M, G, T in (
                (1000, 'B', 'KB', 'MB', 'GB', 'TB'),
                (1024, 'B', 'KiB', 'MiB', 'GiB', 'TiB')):
            Ki, Mi, Gi = step, step * step, step * step * step
            for before, after in (
                    (0, '0' + B), (512, '512' + B), (
                        Ki - 1, '%s%s' % (step - 1, B)),
                    (Ki, '1' + K), (42 * Ki, '42' + K), (
                        Mi - 1, '%s.99%s' % (step - 1, K)),
                    (Mi, '1' + M), (42 * Mi, '42' + M), (
                        Ki * Mi - 1, '%s.99%s' % (step - 1, M)),
                    (Gi, '1' + G), (42 * Gi, '42' + G), (
                        Mi * Mi - 1, '%s.99%s' % (step - 1, G)),
                    (Mi * Mi, '1' + T), (42 * Mi * Mi, '42' + T), (
                        Mi * Gi - 1, '%s.99%s' % (step - 1, T)), (
                        42 * Mi * Gi, '%s%s' % (42 * Ki, T))):
                self.assertEqual(format_size(before, step == 1000), after)

    def test_to_bytes(self):
        from kamaki.cli.utils import to_bytes
        for v in ('wrong', 'KABUM', 'kbps', 'kibps'):
            self.assertRaises(ValueError, to_bytes, v, 'B')
            self.assertRaises(ValueError, to_bytes, 42, v)
        for v in ([1, 2, 3], ('kb', 'mb'), {'kb': 1, 'byte': 2}):
            self.assertRaises(TypeError, to_bytes, v, 'B')
            self.assertRaises(AttributeError, to_bytes, 42, v)
        kl, ki = 1000, 1024
        for size, (unit, factor) in product(
                (0, 42, 3.14, 1023, 10000),
                (
                    ('B', 1), ('b', 1),
                    ('KB', kl), ('KiB', ki),
                    ('mb', kl * kl), ('mIb', ki * ki),
                    ('gB', kl * kl * kl), ('GIB', ki * ki * ki),
                    ('TB', kl * kl * kl * kl), ('tiB', ki * ki * ki * ki))):
            self.assertEqual(to_bytes(size, unit), int(size * factor))

    def test_dict2file(self):
        from kamaki.cli.utils import dict2file, INDENT_TAB
        for d, depth in product((
                    {'k': 42},
                    {'k1': 'v1', 'k2': [1, 2, 3], 'k3': {'k': 'v'}},
                    {'k1': {
                        'k1.1': 'v1.1',
                        'k1.2': [1, 2, 3],
                        'k1.3': {'k': 'v'}}}),
                (-42, 0, 42)):
            exp = ''
            exp_d = []
            exp_l = []
            exp, exp_d, exp_l = '', [], []
            with NamedTemporaryFile() as f:
                for k, v in d.items():
                    sfx = '\n'
                    if isinstance(v, dict):
                        exp_d.append(call(v, f, depth + 1))
                    elif isinstance(v, tuple) or isinstance(v, list):
                        exp_l.append(call(v, f, depth + 1))
                    else:
                        sfx = '%s\n' % v
                    exp += '%s%s: %s' % (
                        ' ' * (depth * INDENT_TAB), k, sfx)
                with patch('kamaki.cli.utils.dict2file') as D2F:
                    with patch('kamaki.cli.utils.list2file') as L2F:
                        dict2file(d, f, depth)
                        f.seek(0)
                        self.assertEqual(f.read(), exp)
                        self.assertEqual(L2F.mock_calls, exp_l)
                        self.assertEqual(D2F.mock_calls, exp_d)

    def test_list2file(self):
        from kamaki.cli.utils import list2file, INDENT_TAB
        for l, depth in product(
                (
                    (1, 2, 3),
                    [1, 2, 3],
                    ('v', [1, 2, 3], (1, 2, 3), {'1': 1, 2: '2', 3: 3}),
                    ['v', {'k1': 'v1', 'k2': [1, 2, 3], 'k3': {1: '1'}}]),
                (-42, 0, 42)):
            with NamedTemporaryFile() as f:
                exp, exp_d, exp_l = '', [], []
                for v in l:
                    if isinstance(v, dict):
                        exp_d.append(call(v, f, depth + 1))
                    elif isinstance(v, list) or isinstance(v, tuple):
                        exp_l.append(call(v, f, depth + 1))
                    else:
                        exp += '%s%s\n' % (' ' * INDENT_TAB * depth, v)
                with patch('kamaki.cli.utils.dict2file') as D2F:
                    with patch('kamaki.cli.utils.list2file') as L2F:
                        list2file(l, f, depth)
                        f.seek(0)
                        self.assertEqual(f.read(), exp)
                        self.assertEqual(L2F.mock_calls, exp_l)
                        self.assertEqual(D2F.mock_calls, exp_d)

    def test__parse_with_regex(self):
        from re import compile as r_compile
        from kamaki.cli.utils import _parse_with_regex
        for args in product(
                (
                    'this is a line',
                    'this_is_also_a_line',
                    'This "text" is quoted',
                    'This "quoted" "text" is more "complicated"',
                    'Is this \'quoted\' text "double \'quoted\' or not?"',
                    '"What \'about\' the" oposite?',
                    ' Try with a " single double quote',
                    'Go "down \'deep " deeper \'bottom \' up" go\' up" !'),
                (
                    '\'.*?\'|".*?"|^[\S]*$',
                    r'"([A-Za-z0-9_\./\\-]*)"',
                    r'\"(.+?)\"',
                    '\\^a\\.\\*\\$')):
            r_parser = r_compile(args[1])
            self.assertEqual(
                _parse_with_regex(*args),
                (r_parser.split(args[0]), r_parser.findall(args[0])))

    def test_split_input(self):
        from kamaki.cli.utils import split_input
        for line, expected in (
                ('unparsable', ['unparsable']),
                ('"parsable"', ['parsable']),
                ('"parse" out', ['parse', 'out']),
                ('"one', ['"one']),
                ('two" or" more"', ['two', ' or', 'more"']),
                ('Go "down \'deep " deeper \'bottom \' up" go\' up" !', [
                    'Go', "down 'deep ", 'deeper', 'bottom ',
                    'up', " go' up", '!']),
                ('Is "this" a \'parsed\' string?', [
                    'Is', 'this', 'a', 'parsed', 'string?'])):
            self.assertEqual(split_input(line), expected)

    @patch('kamaki.cli.utils._readline', return_value='read line')
    @patch('kamaki.cli.utils._flush')
    @patch('kamaki.cli.utils._write')
    def test_ask_user(self, WR, FL, RL):
        from kamaki.cli.utils import ask_user
        msg = 'some question'
        self.assertFalse(ask_user(msg))
        WR.assert_called_once_with('%s [y/N]: ' % msg)
        FL.assert_called_once_with()
        RL.assert_called_once_with()

        self.assertTrue(ask_user(msg, ('r', )))
        self.assertEqual(WR.mock_calls[-1], call('%s [r/N]: ' % msg))
        self.assertEqual(FL.mock_calls, 2 * [call()])
        self.assertEqual(RL.mock_calls, 2 * [call()])

        self.assertTrue(ask_user(msg, ('Z', 'r', 'k')))
        self.assertEqual(WR.mock_calls[-1], call('%s [Z, r, k/N]: ' % msg))
        self.assertEqual(FL.mock_calls, 3 * [call()])
        self.assertEqual(RL.mock_calls, 3 * [call()])

    @patch('kamaki.cli.utils._flush')
    @patch('kamaki.cli.utils._write')
    def test_spiner(self, WR, FL):
        from kamaki.cli.utils import spiner
        spins = ('/', '-', '\\', '|')
        prev = 1
        for i, SP in enumerate(spiner(6)):
            if not i:
                self.assertEqual(WR.mock_calls[-2], call(' '))
            elif i > 5:
                break
            self.assertEqual(SP, None)
            self.assertEqual(WR.mock_calls[-1], call('\b%s' % spins[i % 4]))
            self.assertEqual(FL.mock_calls, prev * [call()])
            prev += 1

    def test_remove_from_items(self):
        from kamaki.cli.utils import remove_from_items
        for v in ('wrong', [1, 2, 3], [{}, 2, {}]):
            self.assertRaises(AssertionError, remove_from_items, v, 'none')
        d = dict(k1=1, k2=dict(k2=2, k3=3), k3=3, k4=4)
        for k in (d.keys() + ['kN']):
            tmp1, tmp2 = dict(d), dict(d)
            remove_from_items([tmp1, ], k)
            tmp1.pop(k, None)
            self.assert_dicts_are_equal(tmp1, tmp2)
        for k in (d.keys() + ['kN']):
            tmp1, tmp2 = dict(d), dict(d)
            remove_from_items([tmp1, tmp2], k)
            self.assert_dicts_are_equal(tmp1, tmp2)

    def test_filter_dicts_by_dict(self):
        from kamaki.cli.utils import filter_dicts_by_dict

        dlist = [
            dict(k1='v1', k2='v2', k3='v3'),
            dict(k1='v1'),
            dict(k2='v2', k3='v3'),
            dict(k1='V1', k3='V3'),
            dict()]
        for l, f, em, cs, exp in (
                (dlist, dlist[2], True, False, dlist[0:1] + dlist[2:3]),
                (dlist, dlist[1], True, False, dlist[0:2] + dlist[3:4]),
                (dlist, dlist[1], True, True, dlist[0:2]),
                (dlist, {'k3': 'v'}, True, False, []),
                (dlist, {'k3': 'v'}, False, False, dlist[0:1] + dlist[2:4]),
                (dlist, {'k3': 'v'}, False, True, dlist[0:1] + dlist[2:3]),
                (dlist, {'k3': 'v'}, True, True, []),
                ):
            self.assertEqual(exp, filter_dicts_by_dict(l, f, em, cs))


if __name__ == '__main__':
    from sys import argv
    from kamaki.cli.test import runTestCase
    runTestCase(UtilsMethods, 'UtilsMethods', argv[1:])
"""
Simplified VM code which works for some cases.
You need extend/rewrite code to pass all cases.
"""

import builtins
import dis
import types
import typing as tp


class Frame:
    """
    Frame header in cpython with description
        https://github.com/python/cpython/blob/3.10/Include/frameobject.h

    Text description of frame parameters
        https://docs.python.org/3/library/inspect.html?highlight=frame#types-and-members
    """

    def __init__(self,
                 frame_code: types.CodeType,
                 frame_builtins: dict[str, tp.Any],
                 frame_globals: dict[str, tp.Any],
                 frame_locals: dict[str, tp.Any]) -> None:
        self.code = frame_code
        self.builtins = frame_builtins
        self.globals = frame_globals
        self.locals = frame_locals
        self.data_stack: tp.Any = []
        self.return_value = None
        self.f_lasti = 0
        self.instructions_offset = {instruction.offset: instruction for instruction in dis.get_instructions(self.code)}

    # Data stack manipulation

    def top(self) -> tp.Any:
        return self.data_stack[-1]

    def topn(self, n: int) -> tp.Any:
        if n > 0:
            return self.data_stack[-n:]
        else:
            return []

    def pop(self) -> tp.Any:
        return self.data_stack.pop()

    def push(self, *values: tp.Any) -> None:
        self.data_stack.extend(values)

    def popn(self, n: int) -> tp.Any:
        """
        Pop a number of values from the value stack.
        A list of n values is returned, the deepest value first.
        """
        if n > 0:
            returned = self.data_stack[-n:]
            self.data_stack[-n:] = []
            return returned
        else:
            return []

    # Run frame

    def run(self) -> tp.Any:
        while self.f_lasti <= max(self.instructions_offset.keys()):
            instruction = self.instructions_offset[self.f_lasti]
            getattr(self, instruction.opname.lower() + "_op")(instruction.argval)
            self.f_lasti += 2
        return self.return_value

    # Load, Store, Delete

    def load_name_op(self, arg: str) -> None:
        if arg in self.locals:
            self.push(self.locals[arg])
        elif arg in self.globals:
            self.push(self.globals[arg])
        elif arg in self.builtins:
            self.push(self.builtins[arg])
        else:
            raise NameError("name \'{arg}\' is not defined")

    def delete_name_op(self, arg: str) -> None:
        del self.locals[arg]

    def store_name_op(self, arg: str) -> None:
        const = self.pop()
        self.locals[arg] = const

    def load_fast_op(self, arg: str) -> None:
        if arg in self.locals:
            self.push(self.locals[arg])
        else:
            raise UnboundLocalError(f'no variable with name \'{arg}\'')

    def store_fast_op(self, arg: str) -> None:
        self.locals[arg] = self.pop()

    def delete_fast_op(self, arg: str) -> None:
        del self.locals[arg]

    def load_global_op(self, arg: str) -> None:
        if arg in self.globals:
            self.push(self.globals[arg])
        elif arg in self.builtins:
            self.push(self.builtins[arg])
        else:
            raise NameError("global name \'{arg}\' is not defined")

    def delete_global_op(self, arg: str) -> None:
        del self.globals[arg]

    def store_global_op(self, arg: str) -> None:
        const = self.pop()
        self.globals[arg] = const

    # def load_deref_op(self, arg: str) -> None:
    #     pass

    # def delete_deref_op(self, arg: str) -> None:
    #     pass

    # def store_deref_op(self, arg: str) -> None:
    #     pass

    def load_build_class_op(self, _: str) -> None:
        self.push(__build_class__)

    # def load_classderef_op(self, i: tp.Any) -> None:
    #     pass

    # def load_closure_op(self, i: tp.Any) -> None:
    #     pass

    def load_attr_op(self, name: tp.Any) -> None:
        obj = self.pop()
        val = getattr(obj, name)
        self.push(val)

    def delete_attr_op(self, name: tp.Any) -> None:
        obj = self.pop()
        delattr(obj, name)

    def store_attr_op(self, name: tp.Any) -> None:
        val, obj = self.popn(2)
        setattr(obj, name, val)

    def load_assertion_error_op(self, message: tp.Any) -> None:
        self.push(AssertionError(message))

    # Compare

    def compare_op_op(self, op: str) -> None:
        left, right = self.popn(2)
        result = False
        if op == "==":
            result = left == right
        elif op == "!=":
            result = left != right
        elif op == ">":
            result = left > right
        elif op == "<":
            result = left < right
        elif op == ">=":
            result = left >= right
        elif op == "<=":
            result = left <= right
        elif op == "in":
            result = left in right
        elif op == "not in":
            result = left not in right
        elif op == "is":
            result = left is right
        elif op == "is not":
            result = left is not right
        else:
            raise TypeError
        self.push(result)

    def is_op_op(self, invert: tp.Any) -> None:
        left, right = self.popn(2)
        if invert:
            self.push(left is not right)
        else:
            self.push(left is right)

    def contains_op_op(self, invert: tp.Any) -> None:
        left, right = self.popn(2)
        if invert:
            self.push(left not in right)
        else:
            self.push(left in right)

    # Unary operations

    def unary_invert_op(self, _: tp.Any) -> None:
        self.push(~self.pop())

    def unary_negative_op(self, _: tp.Any) -> None:
        self.push(-self.pop())

    def unary_not_op(self, _: tp.Any) -> None:
        self.push(not self.pop())

    def unary_positive_op(self, _: tp.Any) -> None:
        self.push(+self.pop())

    def get_iter_op(self, _: tp.Any) -> None:
        self.push(iter(self.pop()))

    # Binary operations

    def binary_add_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left + right)

    def binary_and_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left & right)

    def binary_floor_divide_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left // right)

    def binary_lshift_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left << right)

    def binary_matrix_multiply_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left @ right)

    def binary_modulo_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left % right)

    def binary_multiply_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left * right)

    def binary_or_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left | right)

    def binary_power_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left ** right)

    def binary_rshift_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left >> right)

    def binary_subscr_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left[right])

    def binary_subtract_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left - right)

    def binary_true_divide_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left / right)

    def binary_xor_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        self.push(left ^ right)

    # Inplace operations

    def inplace_add_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left += right
        self.push(left)

    def inplace_and_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left &= right
        self.push(left)

    def inplace_floor_divide_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left //= right
        self.push(left)

    def inplace_lshift_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left <<= right
        self.push(left)

    def inplace_matrix_multiply_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left @= right
        self.push(left)

    def inplace_modulo_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left %= right
        self.push(left)

    def inplace_multiply_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left *= right
        self.push(left)

    def inplace_or_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left |= right
        self.push(left)

    def inplace_power_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left **= right
        self.push(left)

    def inplace_rshift_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left >>= right
        self.push(left)

    def inplace_subtract_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left -= right
        self.push(left)

    def inplace_true_divide_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left /= right
        self.push(left)

    def inplace_xor_op(self, _: tp.Any) -> None:
        left, right = self.popn(2)
        left ^= right
        self.push(left)

    def store_subscr_op(self, _: tp.Any) -> None:
        val, obj, subscr = self.popn(3)
        obj[subscr] = val

    def delete_subscr_op(self, _: tp.Any) -> None:
        obj, subscr = self.popn(2)
        del obj[subscr]

    # Stack manipulation

    def load_const_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.10.6/library/dis.html#opcode-LOAD_CONST

        Operation realization:
            https://github.com/python/cpython/blob/3.10/Python/ceval.c#L1871
        """
        self.push(arg)

    # General instructions

    def nop_op(self, _: tp.Any) -> None:
        pass

    def pop_top_op(self, _: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.10.6/library/dis.html#opcode-POP_TOP

        Operation realization:
            https://github.com/python/cpython/blob/3.10/Python/ceval.c#L1886
        """
        self.pop()

    def rot_n_op(self, n: int) -> None:
        first = self.pop()
        others = self.popn(n - 1)
        self.push(first)
        for i in others:
            self.push(i)

    def rot_two_op(self, _: tp.Any) -> None:
        self.rot_n_op(2)

    def rot_three_op(self, _: tp.Any) -> None:
        self.rot_n_op(3)

    def rot_four_op(self, _: tp.Any) -> None:
        self.rot_n_op(4)

    def dup_top_op(self, _: tp.Any) -> None:
        self.push(self.top())

    def dup_top_two_op(self, _: tp.Any) -> None:
        for i in self.topn(2):
            self.push(i)

    def unpack_sequence_op(self, _: int) -> None:
        tos = self.pop()
        for elem in reversed(tos):
            self.push(elem)

    def unpack_ex_op(self, count: int) -> None:
        tos = self.pop()
        lowbyte = count & 0xFF
        highbyte = (count >> 8) & 0xFF
        for elem in reversed(tos[highbyte + 1:]):
            self.push(elem)
        for elem in reversed(tos[lowbyte]):
            self.push(elem)
        for elem in reversed(tos[:lowbyte]):
            self.push(elem)

    def setup_annotations_op(self, _: tp.Any) -> None:
        if not hasattr(self.locals, '__annotations__'):
            self.locals['__annotations__'] = {}

    def setup_with_op(self, delta: tp.Any) -> None:
        tos = self.pop()
        self.push(tos.__exit__)
        self.push(tos.__enter__())

    def format_value_op(self, func: tp.Any) -> None:
        flags = func[1]
        # if (flags & 0x04) == 0x04:
        #     fmt_spec = self.pop()
        # else:
        #     fmt_spec = None
        value = self.pop()
        if (flags & 0x03) == 0x00:  # value is formatted as-is.
            pass
        if (flags & 0x03) == 0x01:  # call str() on value before formatting it.
            value = str(value)
        if (flags & 0x03) == 0x02:  # call repr() on value before formatting it.
            value = repr(value)
        if (flags & 0x03) == 0x03:  # call ascii() on value before formatting it.
            value = ascii(value)
        result = value
        if func[0] is not None:
            result = func[0](value)
        self.push(result)

    # Functions

    def import_from_op(self, namei: str) -> None:
        f = self.top()
        self.push(getattr(f, namei))

    def import_name_op(self, namei: str) -> None:
        level, fromlist = self.popn(2)
        self.push(__import__(namei, self.globals, self.locals, fromlist, level))

    def import_star_op(self, namei: str) -> None:
        f = self.pop()
        for elem in dir(f):
            if elem[0] != '_':
                self.locals[elem] = getattr(f, elem)

    def arg_binding(argdef: tp.Any, kwdef: tp.Any, code: tp.Any, *args: tp.Any, **kwargs: tp.Any) -> dict[str, tp.Any]:
        CO_VARARGS = 4
        CO_VARKEYWORDS = 8

        ERR_TOO_MANY_POS_ARGS = 'Too many positional arguments'
        ERR_TOO_MANY_KW_ARGS = 'Too many keyword arguments'
        ERR_MULT_VALUES_FOR_ARG = 'Multiple values for arguments'
        ERR_MISSING_POS_ARGS = 'Missing positional arguments'
        ERR_MISSING_KWONLY_ARGS = 'Missing keyword-only arguments'
        ERR_POSONLY_PASSED_AS_KW = 'Positional-only argument passed as keyword argument'

        varnames = code.co_varnames
        argcount = code.co_argcount
        posonlyargcount = code.co_posonlyargcount
        kwonlyargcount = code.co_kwonlyargcount
        defaults = argdef
        kwdefaults = kwdef
        flag_varargs = code.co_flags & CO_VARARGS
        flag_varkwargs = code.co_flags & CO_VARKEYWORDS

        result: dict[str, tp.Any] = {}
        if len(varnames) == 0:
            return result

        posonly = varnames[:posonlyargcount]
        poskw = varnames[posonlyargcount:argcount]
        kwonly = varnames[argcount:(argcount + kwonlyargcount)]
        other = varnames[(argcount + kwonlyargcount):]

        if len(args) > argcount and not flag_varargs:
            raise TypeError(ERR_TOO_MANY_POS_ARGS)

        if not flag_varkwargs:
            for key in kwargs.keys():
                if key not in varnames:
                    raise TypeError(ERR_TOO_MANY_KW_ARGS)
                if key in posonly:
                    raise TypeError(ERR_POSONLY_PASSED_AS_KW)

        args_list = list(args)
        if defaults is not None:
            defaults_dict = dict(zip(reversed(posonly + poskw), reversed(defaults)))
        else:
            defaults_dict = {}
        for elem in posonly:
            if len(args_list):
                result[elem] = args_list.pop(0)
            elif elem in defaults_dict.keys():
                result[elem] = defaults_dict[elem]
            else:
                raise TypeError(ERR_MISSING_POS_ARGS)

        for elem in poskw:
            if len(args_list):
                result[elem] = args_list.pop(0)
                if elem in kwargs.keys():
                    raise TypeError(ERR_MULT_VALUES_FOR_ARG)
            elif elem in kwargs.keys():
                result[elem] = kwargs.pop(elem)
            elif elem in defaults_dict.keys():
                result[elem] = defaults_dict[elem]
            else:
                raise TypeError(ERR_MISSING_POS_ARGS)

        for elem in kwonly:
            if elem in kwargs:
                result[elem] = kwargs.pop(elem)
            elif kwdefaults is not None:
                if elem not in kwdefaults.keys():
                    raise TypeError(ERR_MISSING_KWONLY_ARGS)
                else:
                    result[elem] = kwdefaults[elem]
            else:
                raise TypeError(ERR_MISSING_KWONLY_ARGS)

        if flag_varargs and flag_varkwargs:
            result[other[0]] = tuple(args_list)
            result[other[1]] = kwargs
        else:
            if flag_varargs:
                result[other[0]] = tuple(args_list)
            if flag_varkwargs:
                result[other[0]] = kwargs

        return result

    def make_function_op(self, arg: int) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.10.6/library/dis.html#opcode-MAKE_FUNCTION

        Operation realization:
            https://github.com/python/cpython/blob/3.10/Python/ceval.c#L4290

        Parse stack:
            https://github.com/python/cpython/blob/3.10/Objects/call.c#L612

        Call function in cpython:
            https://github.com/python/cpython/blob/3.10/Python/ceval.c#L4209
        """
        name = self.pop()  # the qualified name of the function (at TOS)  # noqa
        code = self.pop()  # the code associated with the function (at TOS1)

        # if arg & 0x08 == 0x08:
        #     self.pop()
        # if arg & 0x04 == 0x04:
        #     self.pop()
        # if arg & 0x02 == 0x02:
        #     kwdefaults = self.pop()
        # else:
        #     kwdefaults = None
        # if arg & 0x01 == 0x01:
        #     defaults = self.pop()
        # else:
        #     defaults = None

        def f(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
            # TODO: parse input arguments using code attributes such as co_argcount

            # parsed_args: dict[str, tp.Any] = {}
            # parsed_args = self.arg_binding(defaults, kwdefaults, code, *args, **kwargs)
            parsed_args: dict[str, tp.Any] = {code.co_varnames[i]: args[i] for i in range(code.co_argcount)}
            f_locals = dict(self.locals)
            f_locals.update(parsed_args)

            frame = Frame(code, self.builtins, self.globals, f_locals)  # Run code in prepared environment
            return frame.run()

        self.push(f)

    def call_function_op(self, arg: int) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.10.6/library/dis.html#opcode-CALL_FUNCTION

        Operation realization:
            https://github.com/python/cpython/blob/3.10/Python/ceval.c#4243
        """
        args = self.popn(arg)
        f = self.pop()
        self.push(f(*args))

    def call_function_kw_op(self, arg: int) -> None:
        kw_tuple = self.pop()
        kw_arguments = self.popn(len(kw_tuple))
        kwargs = dict(zip(kw_tuple, kw_arguments))
        args = self.popn(arg - len(kw_tuple))
        f = self.pop()
        self.push(f(*args, **kwargs))

    def call_function_ex_op(self, flags: int) -> None:
        if flags & 1:
            kwargs = self.pop()
        else:
            kwargs = {}
        args = self.pop()
        f = self.pop()
        self.push(f(*args, **kwargs))

    def load_method_op(self, namei: tp.Any) -> None:
        tos = self.pop()
        if hasattr(tos, namei):
            val = getattr(tos, namei)
            self.push(val)
        else:
            self.push(None)

    def call_method_op(self, arg: tp.Any) -> None:
        args = self.popn(arg)
        f = self.pop()
        if f is None:
            self.push(None)
        else:
            self.push(f(*args))

    def return_value_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.10.6/library/dis.html#opcode-RETURN_VALUE

        Operation realization:
            https://github.com/python/cpython/blob/3.10/Python/ceval.c#L2436
        """
        self.return_value = self.pop()

    # Building

    def build_const_key_map_op(self, count: int) -> None:
        keys = self.pop()
        values = self.popn(count)
        self.push(dict(zip(keys, values)))

    def build_list_op(self, count: int) -> None:
        self.push(list(self.popn(count)))

    def build_map_op(self, count: int) -> None:
        elements = self.popn(2 * count)
        self.push(dict(zip(elements[::2], elements[1::2])))

    def build_set_op(self, count: int) -> None:
        self.push(set(self.popn(count)))

    def build_slice_op(self, argc: int) -> None:
        if argc == 2:
            start, stop = self.popn(2)
            self.push(slice(start, stop))
        elif argc == 3:
            start, stop, step = self.popn(3)
            self.push(slice(start, stop, step))
        else:
            raise ValueError(f'Invalid \'{argc}\'')

    def build_string_op(self, argc: int) -> None:
        self.push("".join(self.popn(argc)))

    def build_tuple_op(self, count: int) -> None:
        self.push(tuple(self.popn(count)))

    def dict_update_op(self, i: tp.Any) -> None:
        tos = self.pop()
        dict.update(self.data_stack[-i], tos)

    def dict_merge_op(self, i: tp.Any) -> None:
        tos = self.pop()
        if tos in dict(self.data_stack[-i]).keys():
            dict.update(self.data_stack[-i], tos)
        else:
            raise ValueError(f'\'{tos}\' exists')

    def set_update_op(self, i: tp.Any) -> None:
        tos = self.pop()
        set.update(self.data_stack[-i], tos)

    def set_add_op(self, i: tp.Any) -> None:
        tos = self.pop()
        set.add(self.data_stack[-i], tos)

    def list_append_op(self, i: tp.Any) -> None:
        tos = self.pop()
        list.append(self.data_stack[-i], tos)

    def list_extend_op(self, i: tp.Any) -> None:
        tos = self.pop()
        list.extend(self.data_stack[-i], tos)

    def list_to_tuple_op(self, _: tp.Any) -> None:
        self.push(tuple(self.pop()))

    def map_add_op(self, i: tp.Any) -> None:
        tos1, tos = self.popn(2)
        dict.__setitem__(self.data_stack[-i], tos1, tos)

    # Blocks

    # def pop_block_op(self, _: tp.Any) -> None:
    #     pass

    # def pop_except_op(self, _: tp.Any) -> None:
    #     pass

    # def raise_varargs_op(self, arg: tp.Any) -> None:
    #     pass

    # def reraise_op(self, arg: tp.Any) -> None:
    #     pass

    # Jumps

    def jump_absolute_op(self, target: int) -> None:
        self.f_lasti = target - 2

    def jump_forward_op(self, delta: int) -> None:
        self.f_lasti += delta

    def jump_if_false_or_pop_op(self, target: int) -> None:
        if not self.top():
            self.jump_absolute_op(target)
        else:
            self.pop()

    def jump_if_true_or_pop_op(self, target: int) -> None:
        if self.top():
            self.jump_absolute_op(target)
        else:
            self.pop()

    def jump_if_not_exc_match_op(self, target: int) -> None:
        tos1, tos = self.popn(2)
        if tos1 is not tos:
            self.jump_absolute_op(target)

    def pop_jump_if_false_op(self, target: int) -> None:
        if not self.pop():
            self.jump_absolute_op(target)

    def pop_jump_if_true_op(self, target: int) -> None:
        if self.pop():
            self.jump_absolute_op(target)

    def for_iter_op(self, delta: tp.Any) -> None:
        tos = self.top()
        try:
            self.push(next(tos))
        except StopIteration:
            self.pop()
            self.jump_absolute_op(delta)


class VirtualMachine:
    def run(self, code_obj: types.CodeType) -> None:
        """
        :param code_obj: code for interpreting
        """
        globals_context: dict[str, tp.Any] = {}
        frame = Frame(code_obj, builtins.globals()['__builtins__'], globals_context, globals_context)
        return frame.run()

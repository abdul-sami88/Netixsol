"""
44 Python Concepts Definitions for Ilm Academy AI Tutor.
Contains rich metadata, module categories, Bloom's targets, difficulties, and prerequisite dependencies.
"""

CONCEPTS = [
    # Module 1: Basics & Primitives
    {
        "id": "variables",
        "name": "Variables & Name Binding",
        "module": "1_Basics_Primitives",
        "description": "Variable assignment, identifier naming rules, dynamic references in memory.",
        "difficulty": 1,
        "estimated_minutes": 20,
        "bloom_target": "Remembering",
        "prerequisites": []
    },
    {
        "id": "integers_floats",
        "name": "Integers & Floating-Point Numbers",
        "module": "1_Basics_Primitives",
        "description": "Arithmetic operations (+, -, *, /, //, %, **), numeric precision, IEEE 754 floats.",
        "difficulty": 1,
        "estimated_minutes": 25,
        "bloom_target": "Understanding",
        "prerequisites": ["variables"]
    },
    {
        "id": "strings",
        "name": "String Literals & Indexing",
        "module": "1_Basics_Primitives",
        "description": "Single/double/triple quotes, string length len(), zero-based character indexing.",
        "difficulty": 1,
        "estimated_minutes": 25,
        "bloom_target": "Remembering",
        "prerequisites": ["variables"]
    },
    {
        "id": "type_casting",
        "name": "Type Conversion & Casting",
        "module": "1_Basics_Primitives",
        "description": "Explicit conversion between int, float, str, and handling TypeError on incompatible operations.",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["variables", "integers_floats", "strings"]
    },
    {
        "id": "string_formatting",
        "name": "String Formatting & F-Strings",
        "module": "1_Basics_Primitives",
        "description": "Interpolating expressions in f-strings, format specifiers (.2f, :>10), str.format().",
        "difficulty": 2,
        "estimated_minutes": 25,
        "bloom_target": "Applying",
        "prerequisites": ["strings", "type_casting"]
    },

    # Module 2: Control Flow & Logic
    {
        "id": "comparison_operators",
        "name": "Relational & Comparison Operators",
        "module": "2_Control_Flow",
        "description": "Evaluating expressions with ==, !=, <, <=, >, >=, and chained comparisons (0 < x < 10).",
        "difficulty": 1,
        "estimated_minutes": 20,
        "bloom_target": "Understanding",
        "prerequisites": ["integers_floats"]
    },
    {
        "id": "booleans",
        "name": "Booleans & Truthiness",
        "module": "2_Control_Flow",
        "description": "Boolean values True/False, truth value testing of numbers, strings, and empty objects.",
        "difficulty": 2,
        "estimated_minutes": 25,
        "bloom_target": "Understanding",
        "prerequisites": ["comparison_operators"]
    },
    {
        "id": "logical_operators",
        "name": "Logical Operators & Short-Circuiting",
        "module": "2_Control_Flow",
        "description": "Combining conditions with 'and', 'or', 'not', truth tables, short-circuit evaluation semantics.",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Analyzing",
        "prerequisites": ["booleans"]
    },
    {
        "id": "if_else",
        "name": "Conditional If-Else Branching",
        "module": "2_Control_Flow",
        "description": "Binary decision branches, block indentation syntax, conditional execution paths.",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["logical_operators"]
    },
    {
        "id": "elif_chains",
        "name": "Elif Multi-Way Decision Chains",
        "module": "2_Control_Flow",
        "description": "Cascading branches with elif, sequential condition checking, mutually exclusive execution.",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["if_else"]
    },
    {
        "id": "pass_statement",
        "name": "The Pass Placeholder Statement",
        "module": "2_Control_Flow",
        "description": "Syntactic no-op statement for unwritten branch stubs and empty class/function scaffolds.",
        "difficulty": 1,
        "estimated_minutes": 15,
        "bloom_target": "Remembering",
        "prerequisites": ["if_else"]
    },

    # Module 3: Iteration & Sequences
    {
        "id": "while_loops",
        "name": "While Loops & State Iteration",
        "module": "3_Iteration",
        "description": "Repeating execution while condition holds true, loop counters, avoiding infinite loops.",
        "difficulty": 2,
        "estimated_minutes": 35,
        "bloom_target": "Applying",
        "prerequisites": ["if_else"]
    },
    {
        "id": "range_function",
        "name": "Range Sequence Generation",
        "module": "3_Iteration",
        "description": "Arithmetic progression generation using range(start, stop, step), memory-efficient lazy sequences.",
        "difficulty": 2,
        "estimated_minutes": 25,
        "bloom_target": "Understanding",
        "prerequisites": ["integers_floats", "while_loops"]
    },
    {
        "id": "for_loops",
        "name": "For Loops & Iterable Traversal",
        "module": "3_Iteration",
        "description": "Definite iteration over sequences, strings, and range objects using the for-in syntax.",
        "difficulty": 2,
        "estimated_minutes": 35,
        "bloom_target": "Applying",
        "prerequisites": ["range_function"]
    },
    {
        "id": "break_continue",
        "name": "Loop Controls: Break & Continue",
        "module": "3_Iteration",
        "description": "Premature termination with break, skipping remaining statements in pass with continue.",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["while_loops", "for_loops"]
    },
    {
        "id": "nested_loops",
        "name": "Nested Loops & Matrix Traversal",
        "module": "3_Iteration",
        "description": "Hierarchical iteration (outer and inner loops), 2D grid processing, algorithmic complexity O(n^2).",
        "difficulty": 3,
        "estimated_minutes": 45,
        "bloom_target": "Analyzing",
        "prerequisites": ["for_loops"]
    },
    {
        "id": "for_else",
        "name": "Loop Else Clause",
        "module": "3_Iteration",
        "description": "The for-else construct executing only when a loop completes without hitting a break statement.",
        "difficulty": 3,
        "estimated_minutes": 25,
        "bloom_target": "Understanding",
        "prerequisites": ["break_continue"]
    },

    # Module 4: Functions & Modularity
    {
        "id": "functions_def",
        "name": "Function Definitions & Calls",
        "module": "4_Functions",
        "description": "Encapsulating logic using def, function signature, calling syntax, docstrings.",
        "difficulty": 2,
        "estimated_minutes": 35,
        "bloom_target": "Applying",
        "prerequisites": ["if_else", "variables"]
    },
    {
        "id": "arguments_parameters",
        "name": "Parameters & Positional/Keyword Arguments",
        "module": "4_Functions",
        "description": "Formal parameters vs actual arguments, keyword arguments, default parameters.",
        "difficulty": 2,
        "estimated_minutes": 35,
        "bloom_target": "Applying",
        "prerequisites": ["functions_def"]
    },
    {
        "id": "return_statement",
        "name": "Return Statement & Value Passing",
        "module": "4_Functions",
        "description": "Passing computed results to caller vs printing to stdout, multiple return values, None return.",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Analyzing",
        "prerequisites": ["functions_def"]
    },
    {
        "id": "variable_scope",
        "name": "Variable Scope & LEGB Rule",
        "module": "4_Functions",
        "description": "Local, Enclosing, Global, Built-in namespaces, lifetime of local variables, global keyword.",
        "difficulty": 3,
        "estimated_minutes": 40,
        "bloom_target": "Analyzing",
        "prerequisites": ["functions_def", "return_statement"]
    },
    {
        "id": "args_kwargs",
        "name": "Arbitrary Arguments (*args & **kwargs)",
        "module": "4_Functions",
        "description": "Variadic positional arguments (*args tuple) and keyword arguments (**kwargs dictionary).",
        "difficulty": 3,
        "estimated_minutes": 35,
        "bloom_target": "Applying",
        "prerequisites": ["arguments_parameters"]
    },
    {
        "id": "lambda_functions",
        "name": "Anonymous Lambda Functions",
        "module": "4_Functions",
        "description": "Single-expression inline functions using lambda, use cases in sorting keys and functional utilities.",
        "difficulty": 3,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["functions_def"]
    },

    # Module 5: Core Data Structures
    {
        "id": "lists",
        "name": "Lists & List Mutation",
        "module": "5_Data_Structures",
        "description": "Dynamic ordered arrays, index mutation, append(), extend(), insert(), pop(), remove().",
        "difficulty": 2,
        "estimated_minutes": 35,
        "bloom_target": "Applying",
        "prerequisites": ["for_loops"]
    },
    {
        "id": "list_slicing",
        "name": "Sequence Slicing & Striding",
        "module": "5_Data_Structures",
        "description": "Extracting sub-sequences with [start:stop:step], negative steps, reversing sequences.",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["lists"]
    },
    {
        "id": "list_comprehensions",
        "name": "List Comprehensions",
        "module": "5_Data_Structures",
        "description": "Declarative syntax [expr for x in seq if cond], replacing map/filter loops pythonically.",
        "difficulty": 3,
        "estimated_minutes": 40,
        "bloom_target": "Creating",
        "prerequisites": ["lists", "for_loops"]
    },
    {
        "id": "tuples",
        "name": "Tuples & Sequence Unpacking",
        "module": "5_Data_Structures",
        "description": "Immutable sequences, parenthesized tuples, tuple unpacking a, b = b, a, memory efficiency.",
        "difficulty": 2,
        "estimated_minutes": 25,
        "bloom_target": "Understanding",
        "prerequisites": ["lists"]
    },
    {
        "id": "enumerate_zip",
        "name": "Enumerate & Zip Iteration",
        "module": "5_Data_Structures",
        "description": "Pairing indices with items via enumerate(), parallel sequence traversal with zip().",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["for_loops", "tuples"]
    },
    {
        "id": "dictionaries",
        "name": "Dictionaries & Key-Value Lookups",
        "module": "5_Data_Structures",
        "description": "Hash maps with unique hashable keys, O(1) average lookup, key-value mutations.",
        "difficulty": 2,
        "estimated_minutes": 35,
        "bloom_target": "Applying",
        "prerequisites": ["lists", "tuples"]
    },
    {
        "id": "dict_methods",
        "name": "Dictionary Methods (.get, .items)",
        "module": "5_Data_Structures",
        "description": "Safe access with .get(key, default), iterating with .items(), .keys(), .values(), .update().",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["dictionaries"]
    },
    {
        "id": "dict_comprehensions",
        "name": "Dictionary Comprehensions",
        "module": "5_Data_Structures",
        "description": "Constructing and transforming dictionaries declaratively: {k: v for k, v in iterable}.",
        "difficulty": 3,
        "estimated_minutes": 35,
        "bloom_target": "Creating",
        "prerequisites": ["dictionaries", "for_loops"]
    },
    {
        "id": "sets",
        "name": "Sets & Set Operations",
        "module": "5_Data_Structures",
        "description": "Unordered unique element collections, fast membership testing, union, intersection, difference.",
        "difficulty": 2,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["lists"]
    },

    # Module 6: Advanced Functional & Iteration
    {
        "id": "iterators_generators",
        "name": "Iterators & Generator Functions",
        "module": "6_Advanced_Tools",
        "description": "The iterator protocol (iter(), next()), lazy evaluation, yield statement, generator expressions.",
        "difficulty": 4,
        "estimated_minutes": 50,
        "bloom_target": "Evaluating",
        "prerequisites": ["functions_def", "for_loops"]
    },
    {
        "id": "map_filter",
        "name": "Map & Filter Built-ins",
        "module": "6_Advanced_Tools",
        "description": "Functional sequence processing: map(fn, seq) and filter(pred, seq) returning lazy iterators.",
        "difficulty": 3,
        "estimated_minutes": 30,
        "bloom_target": "Applying",
        "prerequisites": ["lambda_functions", "lists"]
    },
    {
        "id": "any_all",
        "name": "Any and All Truth Reductions",
        "module": "6_Advanced_Tools",
        "description": "Evaluating collection-wide truthiness: any() for existential and all() for universal checks.",
        "difficulty": 2,
        "estimated_minutes": 20,
        "bloom_target": "Understanding",
        "prerequisites": ["booleans", "lists"]
    },
    {
        "id": "recursion",
        "name": "Recursive Functions",
        "module": "6_Advanced_Tools",
        "description": "Self-referencing function execution, base cases, recursion stack, maximum recursion depth.",
        "difficulty": 4,
        "estimated_minutes": 50,
        "bloom_target": "Analyzing",
        "prerequisites": ["functions_def", "if_else"]
    },
    {
        "id": "decorators",
        "name": "Function Decorators",
        "module": "6_Advanced_Tools",
        "description": "Higher-order functions wrapping behavior, @decorator syntactic sugar, functools.wraps.",
        "difficulty": 5,
        "estimated_minutes": 60,
        "bloom_target": "Creating",
        "prerequisites": ["functions_def", "args_kwargs"]
    },

    # Module 7: Object-Oriented Programming & Systems
    {
        "id": "classes_instances",
        "name": "Classes & Object Instantiation",
        "module": "7_OOP_Systems",
        "description": "Class blueprints, object instances, the self reference binding methods to state.",
        "difficulty": 3,
        "estimated_minutes": 45,
        "bloom_target": "Applying",
        "prerequisites": ["functions_def", "dictionaries"]
    },
    {
        "id": "dunder_init",
        "name": "The __init__ Constructor",
        "module": "7_OOP_Systems",
        "description": "Initializing object state on creation, instance attributes vs class attributes.",
        "difficulty": 3,
        "estimated_minutes": 40,
        "bloom_target": "Applying",
        "prerequisites": ["classes_instances"]
    },
    {
        "id": "oop_methods",
        "name": "Methods: Instance, Class & Static",
        "module": "7_OOP_Systems",
        "description": "Differentiating instance methods (self), class methods (@classmethod cls), and static methods (@staticmethod).",
        "difficulty": 3,
        "estimated_minutes": 45,
        "bloom_target": "Analyzing",
        "prerequisites": ["classes_instances"]
    },
    {
        "id": "oop_inheritance",
        "name": "Inheritance & Polymorphism",
        "module": "7_OOP_Systems",
        "description": "Subclassing, method overriding, super() delegation to parent classes, polymorphic dispatch.",
        "difficulty": 4,
        "estimated_minutes": 55,
        "bloom_target": "Creating",
        "prerequisites": ["classes_instances", "dunder_init"]
    },
    {
        "id": "encapsulation",
        "name": "Encapsulation & Property Decorators",
        "module": "7_OOP_Systems",
        "description": "Information hiding conventions (_protected, __private name mangling), @property getters and setters.",
        "difficulty": 4,
        "estimated_minutes": 45,
        "bloom_target": "Analyzing",
        "prerequisites": ["classes_instances"]
    },
    {
        "id": "try_except",
        "name": "Exception Handling (Try-Except)",
        "module": "7_OOP_Systems",
        "description": "Catching exceptions, specific error handling (ValueError, KeyError), else and finally blocks.",
        "difficulty": 3,
        "estimated_minutes": 40,
        "bloom_target": "Applying",
        "prerequisites": ["if_else", "functions_def"]
    },
    {
        "id": "file_io_context_managers",
        "name": "File I/O & Context Managers",
        "module": "7_OOP_Systems",
        "description": "Reading and writing files with open(), automatic resource cleanup using 'with' statement.",
        "difficulty": 3,
        "estimated_minutes": 40,
        "bloom_target": "Applying",
        "prerequisites": ["try_except", "strings"]
    }
]


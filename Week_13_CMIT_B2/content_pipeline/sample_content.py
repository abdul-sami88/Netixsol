"""
Sample learning content generator for Ilm Academy Python Course.
Generates realistic Whisper transcripts (with timestamps), slide decks, and instructor notes.
"""

SAMPLE_LESSONS = [
    {
        "lesson_id": "L01",
        "title": "Introduction to Python, Variables & Basic Data Types",
        "duration_seconds": 930,
        "concepts": ["variables", "integers_floats", "strings", "booleans", "type_casting", "string_formatting"],
        "transcripts": [
            {"id": 0, "start": 0.0, "end": 14.5, "text": "Welcome to Ilm Academy's Python Mastery. Today in Lesson 1, we begin with variables and fundamental data types."},
            {"id": 1, "start": 14.5, "end": 42.0, "text": "In Python, a variable is a named reference pointing to an object stored in memory. You assign values using the single equals operator."},
            {"id": 2, "start": 42.0, "end": 85.0, "text": "For example, age = 21 assigns an integer. Unlike C or Java, Python is dynamically typed; you don't declare int or float beforehand."},
            {"id": 3, "start": 85.0, "end": 140.0, "text": "Let's inspect the primitive data types: int for whole numbers, float for decimal values like 3.1415, str for text enclosed in quotes, and bool for True or False."},
            {"id": 4, "start": 140.0, "end": 210.0, "text": "Type casting is essential. When reading user input with input(), it always returns a string. If you want to perform math, convert with int() or float()."},
            {"id": 5, "start": 210.0, "end": 280.0, "text": "A common student pitfall is trying to add a string and integer directly: '5' + 5 produces a TypeError: can only concatenate str to str, not int."},
            {"id": 6, "start": 280.0, "end": 360.0, "text": "You can inspect any variable's runtime type using the built-in type() function, and its memory identifier using id()."},
        ],
        "slides": [
            {"slide_number": 1, "title": "Lesson 1: Variables & Primitives", "timestamp": "00:00", "content": "Ilm Academy Python Foundation\n- Dynamic Typing in Python\n- Memory references vs C-style buckets"},
            {"slide_number": 2, "title": "Core Primitive Types", "timestamp": "01:25", "content": "- int: Arbitrary precision integers (e.g. 42)\n- float: IEEE 754 floating point (e.g. 98.6)\n- str: Unicode string sequences\n- bool: True or False (subclass of int)"},
            {"slide_number": 3, "title": "Type Conversion & Input", "timestamp": "02:20", "content": "Explicit casting: int('10'), float('3.5'), str(100)\nWatch out: input() returns str; always cast before numerical operations."},
            {"slide_number": 4, "title": "Common Bugs & TypeError", "timestamp": "03:30", "content": "Implicit conversion does NOT happen between str and numeric types.\n'Total: ' + 50 -> TypeError\nSolution: 'Total: ' + str(50) or f'Total: {50}'"}
        ],
        "notes": [
            {"section": "Pedagogical Note", "content": "Students without prior coding often confuse variable assignment (=) with mathematical equality (==). Emphasize that the right-hand side is evaluated first, then bound to the name on the left."},
            {"section": "Common Misconceptions", "content": "Students assume variables are boxes containing the value. In Python, variables are labels (pointers) to objects in the heap."},
            {"section": "Recommended Practice", "content": "Have learners write 5 conversions between types and inspect the type using type() before and after."}
        ]
    },
    {
        "lesson_id": "L02",
        "title": "Conditionals, Comparison & Boolean Logic",
        "duration_seconds": 1120,
        "concepts": ["comparison_operators", "booleans", "logical_operators", "if_else", "elif_chains"],
        "transcripts": [
            {"id": 0, "start": 0.0, "end": 22.0, "text": "Welcome back. Today we introduce decision-making in code: conditional execution with if, elif, and else statements."},
            {"id": 1, "start": 22.0, "end": 68.0, "text": "Every conditional evaluates an expression to a truth value: True or False. Python uses relational operators ==, !=, <, <=, >, >="},
            {"id": 2, "start": 68.0, "end": 130.0, "text": "Logical operators in Python are english words: 'and', 'or', and 'not'. Remember that 'and' requires both operands to be True, while 'or' requires at least one."},
            {"id": 3, "start": 130.0, "end": 210.0, "text": "Notice Python uses short-circuit evaluation: if the first operand in an 'and' expression is False, Python skips evaluating the second operand entirely."},
            {"id": 4, "start": 210.0, "end": 310.0, "text": "When chaining multiple branches, use elif. The order matters! Python evaluates from top to bottom and stops at the very first branch whose condition evaluates to True."},
            {"id": 5, "start": 310.0, "end": 420.0, "text": "Truthiness: empty collections, 0, None, and empty strings are falsy. Everything else is truthy in Python conditional contexts."},
        ],
        "slides": [
            {"slide_number": 1, "title": "Control Flow: Conditionals", "timestamp": "00:00", "content": "Branching execution paths with boolean evaluations.\nIndentation (4 spaces) defines code blocks."},
            {"slide_number": 2, "title": "Logical Operators & Short-circuiting", "timestamp": "01:08", "content": "and: True only if both true\nor: True if either true\nnot: Inverts boolean\nShort-circuit: False and expr() skips expr()"},
            {"slide_number": 3, "title": "Elif Decision Chains", "timestamp": "03:30", "content": "Order of precedence matters in multi-way branch:\nif score >= 90: 'A'\nelif score >= 80: 'B'\nelse: 'C'"},
            {"slide_number": 4, "title": "Pythonic Truthiness", "timestamp": "05:10", "content": "Falsy values: False, None, 0, 0.0, '', [], (), {}\nTruthy values: non-empty strings, non-zero numbers, populated containers"}
        ],
        "notes": [
            {"section": "Pedagogical Note", "content": "Students frequently forget that 0 < x < 10 is valid chained comparison syntax in Python, which is more readable than x > 0 and x < 10."},
            {"section": "Common Misconceptions", "content": "Writing 'if x == 1 or 2:' thinking it checks if x is 1 or 2. In reality, '2' is truthy so the condition is always True! Teach 'if x in (1, 2):'."}
        ]
    },
    {
        "lesson_id": "L03",
        "title": "Loops: While, For, Range & Iteration Control",
        "duration_seconds": 1280,
        "concepts": ["while_loops", "for_loops", "range_function", "break_continue"],
        "transcripts": [
            {"id": 0, "start": 0.0, "end": 30.0, "text": "In Lesson 3, we master repetition. Loops allow us to execute a block of code multiple times without code duplication."},
            {"id": 1, "start": 30.0, "end": 95.0, "text": "A while loop repeats as long as a condition remains True. Be cautious: if you forget to increment your loop variable, you get an infinite loop."},
            {"id": 2, "start": 95.0, "end": 175.0, "text": "The for loop in Python is a definite loop; it iterates over items in any sequence or iterable using the 'for item in iterable:' syntax."},
            {"id": 3, "start": 175.0, "end": 260.0, "text": "The range() function produces an arithmetic progression. range(stop), range(start, stop), or range(start, stop, step). Note that 'stop' is exclusive!"},
            {"id": 4, "start": 260.0, "end": 360.0, "text": "To control iteration: 'break' terminates the loop immediately, while 'continue' skips the rest of the current iteration and jumps to the next."},
            {"id": 5, "start": 360.0, "end": 480.0, "text": "Python also has a unique 'for-else' construct: the else block executes only if the loop completed naturally without hitting a break statement."},
        ],
        "slides": [
            {"slide_number": 1, "title": "Iteration: While vs For", "timestamp": "00:00", "content": "while: condition-controlled iteration\nfor: collection-controlled sequence traversal"},
            {"slide_number": 2, "title": "The range() Built-in", "timestamp": "02:55", "content": "range(start, stop[, step])\nExclusive stop: range(1, 5) yields 1, 2, 3, 4\nMemory efficient lazy sequence object"},
            {"slide_number": 3, "title": "Loop Control: Break & Continue", "timestamp": "04:20", "content": "break: emergency exit from inner-most loop\ncontinue: abort remainder of current pass, proceed to next iteration"},
            {"slide_number": 4, "title": "Loop Else Clause", "timestamp": "06:00", "content": "for item in items:\n  if target == item: break\nelse: print('Not found!')\nExecutes only if no break was encountered."}
        ],
        "notes": [
            {"section": "Pedagogical Note", "content": "Week 3 dropout cliff often starts here. Students struggle with off-by-one errors in range() and infinite while loops."},
            {"section": "Common Misconceptions", "content": "Modifying a list while iterating over it with a for loop causes skipped items. Explain that iteration tracks index positions."}
        ]
    },
    {
        "lesson_id": "L04",
        "title": "Functions: Parameters, Return Values & Scope",
        "duration_seconds": 1350,
        "concepts": ["functions_def", "arguments_parameters", "return_statement", "variable_scope"],
        "transcripts": [
            {"id": 0, "start": 0.0, "end": 25.0, "text": "Welcome to Lesson 4. We transition from scripting to procedural modular programming using functions."},
            {"id": 1, "start": 25.0, "end": 80.0, "text": "Functions encapsulate reusable logic using the 'def' keyword followed by the function name, parentheses, and colon."},
            {"id": 2, "start": 80.0, "end": 160.0, "text": "Distinguish parameters from arguments. Parameters are the variable names in the definition; arguments are the concrete values passed during invocation."},
            {"id": 3, "start": 160.0, "end": 240.0, "text": "Crucial distinction: print() merely outputs text to standard out, while return passes data back to the caller. A function without return returns None."},
            {"id": 4, "start": 240.0, "end": 350.0, "text": "Understanding variable scope with LEGB rule: Local, Enclosing, Global, Built-in. Local variables created inside a function cease to exist when the function returns."},
            {"id": 5, "start": 350.0, "end": 460.0, "text": "Default arguments: never use mutable objects like lists or dicts as default arguments in Python, because default arguments are evaluated once at definition time."},
        ],
        "slides": [
            {"slide_number": 1, "title": "Defining Functions", "timestamp": "00:00", "content": "def func_name(param1, param2):\n    \"\"\"Docstring explanation\"\"\"\n    return result"},
            {"slide_number": 2, "title": "Print vs Return", "timestamp": "02:40", "content": "print(): side-effect to console, returns None\nreturn: sends value back to caller for variable assignment and calculation"},
            {"slide_number": 3, "title": "Scope & LEGB Rule", "timestamp": "04:00", "content": "L: Local inside function\nE: Enclosing functions\nG: Global module-level\nB: Built-in namespace (len, range, max)"},
            {"slide_number": 4, "title": "Default Arguments Gotcha", "timestamp": "05:50", "content": "def append_item(x, lst=[]): # DANGEROUS! Shared mutable across calls\nCorrect pattern: def append_item(x, lst=None):\n    if lst is None: lst = []"}
        ],
        "notes": [
            {"section": "Pedagogical Note", "content": "The print vs return confusion is one of the highest predictors of early course dropouts. Drill this concept rigorously."},
            {"section": "Common Misconceptions", "content": "Learners try to access local variables outside the function or assume modifying a parameter modifies an immutable primitive globally."}
        ]
    },
    {
        "lesson_id": "L05",
        "title": "Lists, Tuples & List Comprehensions",
        "duration_seconds": 1420,
        "concepts": ["lists", "list_slicing", "list_comprehensions", "tuples", "enumerate_zip"],
        "transcripts": [
            {"id": 0, "start": 0.0, "end": 28.0, "text": "In Lesson 5, we explore ordered sequences: mutable lists and immutable tuples, plus the powerful syntax of list comprehensions."},
            {"id": 1, "start": 28.0, "end": 90.0, "text": "A list is an ordered, mutable sequence of elements created with square brackets. Lists support indexing from 0 and negative indexing from -1."},
            {"id": 2, "start": 90.0, "end": 170.0, "text": "List slicing syntax is list[start:stop:step]. Remember stop is exclusive. list[::-1] provides an idiomatic way to reverse a sequence."},
            {"id": 3, "start": 170.0, "end": 260.0, "text": "Key list methods: append() adds a single element at the end, extend() concatenates an iterable, while pop() removes and returns an item by index."},
            {"id": 4, "start": 260.0, "end": 370.0, "text": "Tuples are immutable; once created with parentheses, you cannot add, remove, or modify elements. This provides memory efficiency and hashability."},
            {"id": 5, "start": 370.0, "end": 490.0, "text": "List comprehensions offer a concise syntax for transforming lists: [expression for item in iterable if condition]. They are faster and more Pythonic than explicit loops."},
        ],
        "slides": [
            {"slide_number": 1, "title": "Lists: Mutable Sequences", "timestamp": "00:00", "content": "nums = [10, 20, 30]\nZero-indexed, dynamic sizing, can hold mixed data types."},
            {"slide_number": 2, "title": "Indexing & Slicing", "timestamp": "01:30", "content": "s[0]: first element, s[-1]: last element\ns[1:4]: elements at indices 1, 2, 3\ns[::-1]: reversed sequence"},
            {"slide_number": 3, "title": "Tuples vs Lists", "timestamp": "04:20", "content": "Tuple: immutable, e.g. point = (10, 20)\nCan be used as dictionary keys (hashable).\nList: mutable, e.g. items = [1, 2]"},
            {"slide_number": 4, "title": "List Comprehensions", "timestamp": "06:10", "content": "Pattern: [func(x) for x in seq if filter(x)]\nExample: squares = [x**2 for x in range(10) if x % 2 == 0]"}
        ],
        "notes": [
            {"section": "Pedagogical Note", "content": "Differentiate between mutating methods that return None (like lst.sort() or lst.append()) and functions that return new lists (like sorted(lst))."},
            {"section": "Common Misconceptions", "content": "Assigning lst2 = lst1 does not make a copy; it creates another reference to the same list in memory! Use lst1.copy() or lst1[:]."}
        ]
    },
    {
        "lesson_id": "L06",
        "title": "Dictionaries, Sets & Hash-based Lookups",
        "duration_seconds": 1290,
        "concepts": ["dictionaries", "sets", "dict_methods", "dict_comprehensions"],
        "transcripts": [
            {"id": 0, "start": 0.0, "end": 24.0, "text": "Welcome to Lesson 6. We examine hash tables in Python: dictionaries for key-value mappings and sets for unique collections."},
            {"id": 1, "start": 24.0, "end": 85.0, "text": "Dictionaries store key-value associations with O(1) average lookup time. Keys must be immutable and hashable; values can be any type."},
            {"id": 2, "start": 85.0, "end": 160.0, "text": "Accessing a non-existent key with dict[key] raises a KeyError. Use dict.get(key, default) to safely handle missing keys without crashing."},
            {"id": 3, "start": 160.0, "end": 250.0, "text": "Iterating over dictionaries: .keys() for keys, .values() for values, and .items() for (key, value) tuple pairs during unpacking."},
            {"id": 4, "start": 250.0, "end": 350.0, "text": "Sets contain unique, unordered elements. They excel at deduplication and set math: union |, intersection &, and difference -."},
            {"id": 5, "start": 350.0, "end": 460.0, "text": "Dictionary comprehensions allow transforming mappings: {k: v**2 for k, v in data.items() if v > 0}."},
        ],
        "slides": [
            {"slide_number": 1, "title": "Dictionaries: Key-Value Stores", "timestamp": "00:00", "content": "student = {'id': 101, 'name': 'Aisha', 'grade': 'A'}\nFast O(1) key lookups via internal hash tables."},
            {"slide_number": 2, "title": "Safe Retrieval with .get()", "timestamp": "01:25", "content": "user_age = profile.get('age', 18)\nPrevents KeyErrors on missing fields."},
            {"slide_number": 3, "title": "Dictionary Iteration Patterns", "timestamp": "02:40", "content": "for key, val in student.items():\n    print(f'{key} -> {val}')"},
            {"slide_number": 4, "title": "Sets & Set Theory", "timestamp": "04:10", "content": "unique_ids = set([1, 2, 2, 3]) # {1, 2, 3}\nOperators: | (union), & (intersection), - (difference)"}
        ],
        "notes": [
            {"section": "Pedagogical Note", "content": "Explain hash collisions and why mutable objects like lists cannot be dictionary keys or set elements."},
            {"section": "Common Misconceptions", "content": "Creating an empty set with {} actually creates an empty dictionary! An empty set must be instantiated using set()."}
        ]
    },
    {
        "lesson_id": "L07",
        "title": "Object-Oriented Programming: Classes, Instances & Inheritance",
        "duration_seconds": 1540,
        "concepts": ["classes_instances", "dunder_init", "oop_methods", "oop_inheritance"],
        "transcripts": [
            {"id": 0, "start": 0.0, "end": 30.0, "text": "Lesson 7 introduces Object-Oriented Programming (OOP) to organize complex code into modular, reusable classes and objects."},
            {"id": 1, "start": 30.0, "end": 105.0, "text": "A class is a blueprint, while an object is an instance created from that blueprint. We define instance attributes inside the __init__ constructor."},
            {"id": 2, "start": 105.0, "end": 190.0, "text": "The first parameter of an instance method is always 'self'. 'self' refers to the specific instance calling the method."},
            {"id": 3, "start": 190.0, "end": 290.0, "text": "Class attributes belong to the class itself and are shared across all instances, whereas instance attributes belong exclusively to each object."},
            {"id": 4, "start": 290.0, "end": 410.0, "text": "Inheritance allows a subclass to inherit attributes and methods from a superclass. We use super().__init__() to invoke the parent constructor."},
            {"id": 5, "start": 410.0, "end": 520.0, "text": "Polymorphism allows subclasses to override methods, providing specialized behavior while maintaining a consistent public interface."},
        ],
        "slides": [
            {"slide_number": 1, "title": "OOP: Blueprints & Objects", "timestamp": "00:00", "content": "class Student:\n    def __init__(self, name, id):\n        self.name = name\n        self.id = id"},
            {"slide_number": 2, "title": "The Role of 'self'", "timestamp": "01:45", "content": "Explicit self parameter binds methods to caller instance.\ns1.speak() translates under the hood to Student.speak(s1)."},
            {"slide_number": 3, "title": "Class vs Instance Attributes", "timestamp": "03:10", "content": "class BankAccount:\n    interest_rate = 0.05 # Class attribute shared by all\n    def __init__(self, bal): self.bal = bal # Instance"},
            {"slide_number": 4, "title": "Inheritance & super()", "timestamp": "04:50", "content": "class GraduateStudent(Student):\n    def __init__(self, name, id, thesis):\n        super().__init__(name, id)\n        self.thesis = thesis"}
        ],
        "notes": [
            {"section": "Pedagogical Note", "content": "Week 6-7 attrition spike is often attributed to OOP abstract syntax. Visualizing memory diagrams of instances referencing class vtables helps."},
            {"section": "Common Misconceptions", "content": "Forgetting 'self.' when accessing instance variables inside methods causes UnboundLocalError or references unexpected global variables."}
        ]
    },
    {
        "lesson_id": "L08",
        "title": "Exception Handling, Context Managers & File I/O",
        "duration_seconds": 1210,
        "concepts": ["try_except", "file_io_context_managers", "iterators_generators", "recursion"],
        "transcripts": [
            {"id": 0, "start": 0.0, "end": 25.0, "text": "In our final foundational lesson, we address writing robust, resilient Python software through exception handling and safe file operations."},
            {"id": 1, "start": 25.0, "end": 90.0, "text": "Uncaught errors terminate program execution. Using try-except blocks allows intercepting exceptions and handling them gracefully."},
            {"id": 2, "start": 90.0, "end": 175.0, "text": "Always catch specific exceptions such as ValueError or FileNotFoundError. Avoid bare 'except:' clauses which silence bugs and capture KeyboardInterrupt."},
            {"id": 3, "start": 175.0, "end": 260.0, "text": "The 'else' block executes only if no exception occurred in 'try', while 'finally' always runs, making it ideal for cleanup."},
            {"id": 4, "start": 260.0, "end": 370.0, "text": "File handling: always use the 'with open(...) as f:' context manager. It guarantees that the file stream is safely closed even if an exception occurs."},
            {"id": 5, "start": 370.0, "end": 480.0, "text": "You can raise exceptions intentionally using 'raise ValueError(...)' or define custom exception hierarchies inheriting from Exception."},
        ],
        "slides": [
            {"slide_number": 1, "title": "Defensive Code: Try-Except", "timestamp": "00:00", "content": "try:\n    val = int(user_input)\nexcept ValueError as e:\n    print(f'Invalid input: {e}')"},
            {"slide_number": 2, "title": "The Full Handler: Try-Except-Else-Finally", "timestamp": "01:30", "content": "try -> risky operation\nexcept -> handle specific error\nelse -> executes only if try succeeded\nfinally -> cleanup always runs"},
            {"slide_number": 3, "title": "Context Managers & with open()", "timestamp": "04:20", "content": "with open('data.txt', 'r', encoding='utf-8') as f:\n    content = f.read()\n# File automatically closed on exit"},
            {"slide_number": 4, "title": "Custom Exceptions", "timestamp": "06:10", "content": "class CourseNotFoundError(Exception):\n    pass\nraise CourseNotFoundError('Course ID does not exist')"}
        ],
        "notes": [
            {"section": "Pedagogical Note", "content": "Demonstrate what happens when files are left open in long-running processes without context managers."},
            {"section": "Common Misconceptions", "content": "Students often put entire scripts inside one giant try block. Keep try blocks as narrow as possible."}
        ]
    }
]

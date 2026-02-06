# Introduction to Python Programming Fundamentals

**Topic:** Python Programming | **Questions:** 10 | **Time:** 20 mins | **Passing:** 70%

---

### Q1. Which of the following is the correct way to assign the value 10 to a variable named 'x' in Python?
*Difficulty: easy | Topic: Variables & Assignment*

- **A)** x = 10
- **B)** x == 10
- **C)** int x = 10
- **D)** assign x to 10

**Answer:** A

**Explanation:** In Python, the single equals sign (=) is used as the assignment operator to give a value to a variable. '==' is for comparison.

---

### Q2. Python uses curly braces {} to define code blocks like functions and loops.
*Difficulty: easy | Topic: Code Structure & Indentation*

- **True)** True
- **False)** False

**Answer:** False

**Explanation:** Python uses indentation (whitespace) to define code blocks, not curly braces. This is a key distinguishing feature of Python's syntax.

---

### Q3. In Python, single-line comments begin with the _________ symbol.
*Difficulty: easy | Topic: Comments*


**Answer:** #

**Explanation:** The '#' symbol is used to denote a single-line comment in Python. Any text following '#' on the same line is ignored by the interpreter.

---

### Q4. What will be the output of the following Python code: my_list = [1, 2, 3]; my_list.append(4); print(my_list[0])?
*Difficulty: medium | Topic: Lists & Indexing*

- **A)** 1
- **B)** 4
- **C)** [1, 2, 3, 4]
- **D)** Error

**Answer:** A

**Explanation:** The `append(4)` method adds 4 to the end of `my_list`. However, `my_list[0]` accesses the element at index 0, which is the first element, so it prints 1.

---

### Q5. How many times will the following loop execute: for i in range(3): print('Hello')?
*Difficulty: medium | Topic: For Loops & Range*

- **A)** 2
- **B)** 3
- **C)** 4
- **D)** 0

**Answer:** B

**Explanation:** The `range(3)` function generates a sequence of numbers from 0 up to (but not including) 3, which are 0, 1, and 2. The loop will iterate once for each of these numbers, totaling 3 executions.

---

### Q6. Once a tuple is created in Python, its elements can be changed (it is mutable).
*Difficulty: medium | Topic: Tuples & Immutability*

- **True)** True
- **False)** False

**Answer:** False

**Explanation:** Tuples are immutable sequences in Python, meaning their elements cannot be changed, added, or removed after the tuple has been created. Lists, in contrast, are mutable.

---

### Q7. The keyword used to define a function in Python is _________.
*Difficulty: medium | Topic: Functions*


**Answer:** def

**Explanation:** The `def` keyword is used to introduce a function definition, followed by the function name, parentheses for parameters, and a colon.

---

### Q8. What value will 'x' have after this code executes: x = 10; def func(): global x; x = 20; func(); print(x)?
*Difficulty: hard | Topic: Global Variables & Scope*

- **A)** 10
- **B)** 20
- **C)** Error
- **D)** None

**Answer:** B

**Explanation:** The `global x` statement inside `func()` explicitly declares that the `x` being modified is the global variable `x`, not a new local variable. Therefore, the global `x` is updated to 20.

---

### Q9. Which of the following will result in a TypeError in Python?
*Difficulty: hard | Topic: Built-in Functions & Error Types*

- **A)** len("hello")
- **B)** len([1,2,3])
- **C)** len(5)
- **D)** len((1,2))

**Answer:** C

**Explanation:** The `len()` function expects an object that has a length (e.g., strings, lists, tuples, dictionaries). An integer like `5` does not have a length, leading to a `TypeError`.

---

### Q10. What is the result of 7 // 2 in Python?
*Difficulty: medium | Topic: Operators*

- **A)** 3.5
- **B)** 3
- **C)** 4
- **D)** 1

**Answer:** B

**Explanation:** The `//` operator performs floor division, which divides the first number by the second and then rounds the result down to the nearest whole number (integer). 7 divided by 2 is 3.5, and flooring it gives 3.

---


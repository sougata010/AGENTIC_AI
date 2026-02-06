# Introduction to Python Programming Quiz

**Topic:** Python Programming Fundamentals | **Questions:** 10 | **Time:** 20 mins | **Passing:** 70%

---

### Q1. Which of the following is the correct way to declare a variable and assign an integer value of 10 in Python?
*Difficulty: easy | Topic: Variables and Data Types*

- **A)** int x = 10;
- **B)** x = 10;
- **C)** variable x = 10;
- **D)** assign x = 10;

**Answer:** B

**Explanation:** In Python, variable declaration is dynamic; you simply assign a value to a variable name without explicitly stating its type. Option B correctly demonstrates this.

---

### Q2. Python uses curly braces {} to define code blocks like loops and functions.
*Difficulty: easy | Topic: Syntax and Structure*

- **A)** True
- **B)** False

**Answer:** False

**Explanation:** Python uses indentation (whitespace) to define code blocks, not curly braces. Curly braces are used for dictionaries and sets.

---

### Q3. The Python keyword used to define a function is _________.
*Difficulty: easy | Topic: Functions*


**Answer:** def

**Explanation:** The 'def' keyword is short for 'define' and is used to create user-defined functions in Python.

---

### Q4. What will be the output of the following Python code snippet?x = [1, 2, 3]y = xprint(y[0])
*Difficulty: medium | Topic: Lists and References*

- **A)** 1
- **B)** [1]
- **C)** Error
- **D)** None

**Answer:** A

**Explanation:** When y = x, y becomes a reference to the same list object that x refers to. y[0] accesses the element at index 0 of that list, which is 1.

---

### Q5. Which of the following is an immutable data type in Python?
*Difficulty: medium | Topic: Data Types*

- **A)** List
- **B)** Dictionary
- **C)** Tuple
- **D)** Set

**Answer:** C

**Explanation:** Tuples are immutable, meaning their elements cannot be changed after creation. Lists, dictionaries, and sets are mutable.

---

### Q6. The 'elif' statement in Python is used to check multiple conditions sequentially after an initial 'if' statement.
*Difficulty: medium | Topic: Control Flow*

- **A)** True
- **B)** False

**Answer:** True

**Explanation:** The 'elif' (else if) statement allows you to check for additional conditions if the preceding 'if' or 'elif' conditions were false.

---

### Q7. To iterate over a sequence of numbers from 0 up to (but not including) 5, you would use the `range()` function as `for i in range(___)`.
*Difficulty: medium | Topic: Loops*


**Answer:** 5

**Explanation:** The `range(n)` function generates numbers from 0 to n-1. So, `range(5)` generates 0, 1, 2, 3, 4.

---

### Q8. What is the primary purpose of a 'try-except' block in Python?
*Difficulty: medium | Topic: Error Handling*

- **A)** To define a new function.
- **B)** To handle errors and exceptions gracefully.
- **C)** To create a loop that runs indefinitely.
- **D)** To import external modules.

**Answer:** B

**Explanation:** The 'try-except' block is Python's mechanism for handling runtime errors (exceptions) without crashing the program, allowing for graceful error recovery.

---

### Q9. Consider the following code:my_list = [1, 2, 3, 4]my_list.append([5, 6])What will be the length of `my_list` after this operation?
*Difficulty: hard | Topic: List Manipulation*

- **A)** 4
- **B)** 5
- **C)** 6
- **D)** Error

**Answer:** B

**Explanation:** The `append()` method adds its argument as a single element to the end of the list. In this case, `[5, 6]` is added as one element, making the list `[1, 2, 3, 4, [5, 6]]`, which has a length of 5.

---

### Q10. In Python, a dictionary stores data as key-value pairs, where each key must be _________.
*Difficulty: hard | Topic: Dictionaries*


**Answer:** unique and immutable

**Explanation:** Dictionary keys must be unique to ensure that each value can be retrieved unambiguously. They must also be immutable (like strings, numbers, or tuples) so their hash value doesn't change, which is crucial for efficient lookup.

---


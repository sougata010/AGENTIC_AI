# Data Structures and Algorithms Fundamentals Quiz

**Topic:** Data Structures and Algorithms (DSA) | **Questions:** 10 | **Time:** 15 mins | **Passing:** 70%

---

### Q1. What is the primary characteristic of an array as a data structure?
*Difficulty: easy | Topic: Arrays*

- **A)** It has a dynamic size that changes automatically.
- **B)** Elements are stored in contiguous memory locations.
- **C)** Elements can only be accessed sequentially.
- **D)** Data is organized in a hierarchical manner.

**Answer:** B

**Explanation:** Arrays store elements in contiguous memory locations, which allows for constant-time (O(1)) random access to any element using its index.

---

### Q2. An algorithm must always terminate after a finite number of steps.
*Difficulty: easy | Topic: Algorithm Basics*

- **A)** True
- **B)** False

**Answer:** True

**Explanation:** One of the fundamental properties of an algorithm is finiteness, meaning it must always complete after a finite number of steps for all valid inputs.

---

### Q3. The notation used to describe the upper bound of an algorithm's running time is called __________.
*Difficulty: easy | Topic: Asymptotic Analysis*


**Answer:** Big O notation

**Explanation:** Big O notation provides an asymptotic upper bound on the growth rate of a function, indicating the maximum time or space an algorithm might take in the worst-case scenario.

---

### Q4. Which data structure is most efficient for inserting and deleting elements at arbitrary positions, given that elements are not frequently accessed by index?
*Difficulty: medium | Topic: Linked Lists*

- **A)** Array
- **B)** Linked List
- **C)** Hash Table
- **D)** Stack

**Answer:** B

**Explanation:** Linked lists allow O(1) insertion and deletion operations (after the position is found), as only pointers need to be updated. Arrays require shifting elements, making these operations O(n).

---

### Q5. What is the worst-case time complexity for Bubble Sort?
*Difficulty: medium | Topic: Sorting Algorithms*

- **A)** O(n log n)
- **B)** O(n)
- **C)** O(n^2)
- **D)** O(log n)

**Answer:** C

**Explanation:** In the worst-case scenario (e.g., a reverse-sorted array), Bubble Sort performs approximately n^2 comparisons and swaps, leading to an O(n^2) time complexity.

---

### Q6. The algorithm used to find the shortest path from a single source vertex to all other vertices in a graph with non-negative edge weights is known as __________ algorithm.
*Difficulty: medium | Topic: Graph Algorithms*


**Answer:** Dijkstra's

**Explanation:** Dijkstra's algorithm is a greedy algorithm that efficiently finds the shortest paths from a single source node to all other nodes in a graph with non-negative edge weights.

---

### Q7. In-order traversal of a Binary Search Tree (BST) always produces elements in sorted order.
*Difficulty: medium | Topic: Trees*

- **A)** True
- **B)** False

**Answer:** True

**Explanation:** By definition, a Binary Search Tree maintains the property that all nodes in the left subtree are smaller than the root, and all nodes in the right subtree are larger. In-order traversal visits the left subtree, then the root, then the right subtree, thus yielding elements in non-decreasing order.

---

### Q8. For implementing an 'undo' functionality in an application, which data structure is most appropriate?
*Difficulty: medium | Topic: Data Structure Applications*

- **A)** Queue
- **B)** Stack
- **C)** Heap
- **D)** Graph

**Answer:** B

**Explanation:** An 'undo' operation requires reversing the most recent action, which follows the Last-In, First-Out (LIFO) principle. A stack is the perfect data structure for LIFO operations.

---

### Q9. Which of the following data structures has an amortized O(1) time complexity for its 'add' (append) operation, but can have a worst-case O(n) complexity?
*Difficulty: hard | Topic: Amortized Analysis*

- **A)** Fixed-size Array
- **B)** Singly Linked List
- **C)** Dynamic Array (e.g., ArrayList, vector)
- **D)** Doubly Linked List

**Answer:** C

**Explanation:** Dynamic arrays (like ArrayList in Java or vector in C++) typically double their capacity when full. This reallocation and copying of elements leads to an O(n) worst-case time for a single 'add' operation, but over a sequence of operations, the average (amortized) time complexity is O(1).

---

### Q10. The Bellman-Ford algorithm is capable of detecting negative cycles in a graph because:
*Difficulty: hard | Topic: Graph Algorithms*

- **A)** It uses a priority queue to optimize path selection.
- **B)** It relaxes edges V-1 times and then checks for further relaxation in the V-th iteration.
- **C)** It only works on Directed Acyclic Graphs (DAGs).
- **D)** It uses a depth-first search approach to explore paths.

**Answer:** B

**Explanation:** The Bellman-Ford algorithm correctly finds shortest paths in V-1 iterations. If, after V-1 iterations, an edge can still be relaxed in the V-th iteration, it implies the existence of a negative cycle reachable from the source vertex.

---


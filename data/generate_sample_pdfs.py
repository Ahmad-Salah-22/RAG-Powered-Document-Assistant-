"""
Generates rich, authentic academic sample PDF documents for testing the RAG pipeline.
Covering:
1. cs_intro_python.pdf - Programming Fundamentals & Object-Oriented Design
2. cs_data_structures.pdf - Data Structures, Algorithms & Complexity
3. cs_machine_learning.pdf - Artificial Intelligence & RAG System Architecture
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def create_pdf(filename: str, title: str, pages_content: list[list[str]]):
    target_path = os.path.join("data", "raw", filename)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        target_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=15
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceAfter=10
    )

    story = []

    for page_idx, page_paragraphs in enumerate(pages_content):
        if page_idx == 0:
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 10))
        
        for p in page_paragraphs:
            if p.startswith("## "):
                story.append(Paragraph(p[3:], heading_style))
            else:
                story.append(Paragraph(p, body_style))
        
        if page_idx < len(pages_content) - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"Generated PDF: {target_path} ({len(pages_content)} pages)")


def generate_all_samples():
    # 1. CS Intro Python (3 Pages)
    cs_python_content = [
        # Page 1
        [
            "## Module 1: Introduction to Computer Science and Python Syntax",
            "Computer science is the study of computation, information processing, and algorithmic problem-solving. Python is a high-level, interpreted programming language widely used in software engineering, data analysis, and artificial intelligence.",
            "Variables in Python serve as named references to objects stored in dynamic memory. Unlike statically typed languages like Java or C++, Python uses dynamic typing, meaning a variable's type is determined at runtime based on the assigned object.",
            "Primitive data types in Python include integers (int), floating-point numbers (float), booleans (bool), and strings (str). Data structures such as lists, tuples, sets, and dictionaries allow developers to organize complex data."
        ],
        # Page 2
        [
            "## Module 2: Control Flow Structures and Functions",
            "Control flow structures dictate the order in which code statements execute. Conditional statements (if, elif, else) evaluate boolean expressions to branch program execution.",
            "Iteration is handled via for-loops and while-loops. A for-loop iterates over sequences such as lists or ranges, whereas a while-loop continues executing as long as a specified condition remains true.",
            "Functions modularize code into reusable blocks. Defined using the 'def' keyword, functions can accept positional and keyword arguments and return values using the 'return' statement. Scope rules in Python follow the LEGB rule (Local, Enclosing, Global, Built-in)."
        ],
        # Page 3
        [
            "## Module 3: Object-Oriented Programming (OOP) Principles",
            "Object-Oriented Programming (OOP) is a design paradigm built around objects containing data and behavior. The core pillars of OOP are Encapsulation, Abstraction, Inheritance, and Polymorphism.",
            "A Class acts as a blueprint for creating objects. The '__init__' initializer method initializes an instance's attributes upon creation. Encapsulation hides internal object implementation details, exposing only necessary interfaces through public methods."
        ]
    ]

    # 2. CS Data Structures (3 Pages)
    cs_ds_content = [
        # Page 1
        [
            "## Lecture 1: Abstract Data Types and Array Data Structures",
            "An Abstract Data Type (ADT) specifies a set of data items and operations without dictating the underlying implementation. Arrays are linear data structures storing elements in contiguous memory locations.",
            "Arrays offer O(1) constant time complexity for random index access. However, inserting or deleting elements from an arbitrary position requires shifting elements, yielding O(n) linear time complexity.",
            "Dynamic arrays, such as Python lists, automatically rescale their internal buffer when capacity is exceeded, providing amortized O(1) append operations."
        ],
        # Page 2
        [
            "## Lecture 2: Hash Tables, Collisions, and Complexity",
            "A Hash Table (or Hash Map) is a dictionary data structure that maps keys to values using a cryptographic or integer hash function. A hash function transforms a key into an array index.",
            "In optimal conditions, Hash Tables provide average-case O(1) constant time complexity for search, insertion, and deletion operations. When two distinct keys produce the same hash index, a collision occurs.",
            "Collision resolution techniques include Separate Chaining (using linked lists at each bucket) and Open Addressing (probing techniques like linear probing, quadratic probing, or double hashing)."
        ],
        # Page 3
        [
            "## Lecture 3: Binary Search Trees and Sorting Algorithms",
            "A Binary Search Tree (BST) is a hierarchical node-based tree structure where the left child's key is strictly less than its parent's key, and the right child's key is greater than or equal.",
            "For a balanced BST (such as an AVL tree or Red-Black tree), search, insertion, and deletion exhibit O(log n) logarithmic time complexity. In an unbalanced degenerate tree, performance degrades to O(n).",
            "Sorting algorithms reorder datasets. QuickSort and MergeSort operate via divide-and-conquer with average time complexity of O(n log n). MergeSort is stable and guarantees O(n log n) worst-case performance."
        ]
    ]

    # 3. CS Machine Learning & RAG (3 Pages)
    cs_ml_content = [
        # Page 1
        [
            "## Chapter 1: Introduction to Machine Learning and Neural Networks",
            "Machine Learning (ML) is a branch of artificial intelligence that enables systems to automatically learn patterns from data without being explicitly programmed.",
            "Supervised learning trains models on labeled datasets to predict continuous targets (regression) or discrete categories (classification). Unsupervised learning discovers hidden structures in unlabeled data through techniques like K-Means clustering and Principal Component Analysis (PCA).",
            "Neural Networks consist of interconnected nodes (neurons) structured in input, hidden, and output layers. Weights are optimized via gradient descent and backpropagation."
        ],
        # Page 2
        [
            "## Chapter 2: Natural Language Processing and Embeddings",
            "Natural Language Processing (NLP) focuses on enabling computers to understand, analyze, and generate human text.",
            "Embedding models (such as Sentence-Transformers) convert raw text into dense, continuous numerical vector representations in high-dimensional space. Semantically similar sentences map to nearby vector coordinates.",
            "Cosine similarity measures the angle between two embedding vectors. A cosine distance near 0 indicates high semantic similarity, enabling efficient nearest-neighbor search in vector databases."
        ],
        # Page 3
        [
            "## Chapter 3: Retrieval-Augmented Generation (RAG) Architecture",
            "Retrieval-Augmented Generation (RAG) combines dense vector retrieval with Large Language Models (LLMs) to produce accurate, factual responses grounded in external domain documents.",
            "The standard RAG pipeline operates as follows: 1) Document text extraction and chunking, 2) Dense vector embedding generation, 3) Persistence in a vector database like ChromaDB, 4) Top-K vector similarity retrieval for user questions, and 5) LLM response generation constrained by retrieved context.",
            "RAG mitigates LLM hallucinations, eliminates expensive fine-tuning for dynamic knowledge, and provides transparent source attribution with document and page citations."
        ]
    ]

    create_pdf("cs_intro_python.pdf", "CS 101: Computer Science & Python Programming", cs_python_content)
    create_pdf("cs_data_structures.pdf", "CS 201: Data Structures & Algorithm Analysis", cs_ds_content)
    create_pdf("cs_machine_learning.pdf", "CS 301: Machine Learning & RAG Architecture", cs_ml_content)


if __name__ == "__main__":
    generate_all_samples()

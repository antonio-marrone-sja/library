CREATE DATABASE IF NOT EXISTS library_management;

USE library_management;

CREATE TABLE books (
    book_id INT AUTO_INCREMENT,
    isbn VARCHAR(20) NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(150) NOT NULL,
    publication_year SMALLINT NULL,
    cover_image VARCHAR(255) NULL,

    CONSTRAINT pk_books
    PRIMARY KEY (book_id),

    CONSTRAINT unique_books_isbn
    UNIQUE (isbn)
);

CREATE TABLE members (
    member_id INT AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email varchar(255) NOT NULL,
    registration_date DATE NOT NULL,

    CONSTRAINT pk_members
    PRIMARY KEY (member_id),

    CONSTRAINT unique_members_email
    UNIQUE (email)
);

CREATE TABLE book_copies (
    copy_id INT AUTO_INCREMENT,
    book_id INT NOT NULL,
    acquisition_date DATE NULL,
    status VARCHAR(20) NOT NULL,

    CONSTRAINT pk_book_copies
    PRIMARY KEY (copy_id),

    CONSTRAINT fk_book_copies_book
    FOREIGN KEY (book_id) REFERENCES books(book_id),

    CONSTRAINT check_book_copies_status
    CHECK (status IN ('available', 'on_loan', 'withdrawn'))
);

CREATE TABLE loans (
    loan_id INT AUTO_INCREMENT,
    copy_id INT NOT NULL,
    member_id INT NOT NULL,
    loan_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,

    CONSTRAINT pk_loans
    PRIMARY KEY (loan_id),

    CONSTRAINT fk_loans_copy
    FOREIGN KEY (copy_id) REFERENCES book_copies(copy_id),

    CONSTRAINT fk_loans_member
    FOREIGN KEY (member_id) REFERENCES members(member_id),

    CONSTRAINT check_loans_due_date
    CHECK (due_date >= loan_date),

    CONSTRAINT check_loans_return_date
    CHECK (return_date IS NULL OR return_date >= loan_date)
);
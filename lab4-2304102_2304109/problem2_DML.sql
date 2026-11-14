USE library;

-- 5 authors: two from Egypt, two from the UK; author 5 has no books
INSERT INTO author (author_id, name, country) VALUES
    (1, 'Naguib Mahfouz',  'Egypt'),
    (2, 'Taha Hussein',    'Egypt'),
    (3, 'Agatha Christie', 'United Kingdom'),
    (4, 'George Orwell',   'United Kingdom'),
    (5, 'Haruki Murakami', 'Japan');

-- 3 publishers (Egypt and United Kingdom match some authors)
INSERT INTO publisher (publisher_id, name, country) VALUES
    (1, 'Dar El Shorouk', 'Egypt'),
    (2, 'Penguin Books',  'United Kingdom'),
    (3, 'Harper Collins', 'United States');

-- 3 categories
INSERT INTO category (category_id, name) VALUES
    (1, 'Fiction'),
    (2, 'Mystery'),
    (3, 'History');

-- 10 books (book 6 costs 18.25 -> between 15 and 20; books 7 and 10 are never borrowed)
INSERT INTO book (book_id, title, price, publish_year, author_id, publisher_id, category_id) VALUES
    (1,  'Palace Walk',                  14.50, 1956, 1, 1, 1),
    (2,  'Midaq Alley',                  12.00, 1947, 1, 1, 1),
    (3,  'Children of Gebelawi',         16.75, 1959, 1, 1, 1),
    (4,  'The Days',                     15.50, 1929, 2, 1, 3),
    (5,  'Murder on the Orient Express', 11.99, 1934, 3, 2, 2),
    (6,  'And Then There Were None',     18.25, 1939, 3, 2, 2),
    (7,  'The ABC Murders',              10.50, 1936, 3, 3, 2),
    (8,  '1984',                         13.00, 1949, 4, 2, 1),
    (9,  'Animal Farm',                   9.99, 1945, 4, 2, 1),
    (10, 'Homage to Catalonia',          14.99, 1938, 4, 3, 3);

-- 5 members (member 5 has no loans)
INSERT INTO member (member_id, name, email, join_date) VALUES
    (1, 'Sara Ali',     'sara@mail.com',    '2026-01-10'),
    (2, 'Omar Hassan',  'omar@mail.com',    '2026-02-15'),
    (3, 'Mona Said',    'mona@mail.com',    '2026-03-20'),
    (4, 'Youssef Adel', 'youssef@mail.com', '2026-05-05'),
    (5, 'Laila Karim',  'laila@mail.com',   '2026-06-30');

-- 12 loans (return_date NULL = not returned yet: loans 3, 7, 9, 12)
INSERT INTO loan (loan_id, book_id, member_id, loan_date, return_date) VALUES
    (1,  1, 1, '2026-09-01', '2026-09-10'),
    (2,  1, 2, '2026-09-12', '2026-09-20'),
    (3,  1, 3, '2026-10-01', NULL),
    (4,  5, 1, '2026-09-05', '2026-09-15'),
    (5,  5, 2, '2026-09-25', '2026-10-02'),
    (6,  8, 1, '2026-09-15', '2026-09-22'),
    (7,  8, 4, '2026-10-03', NULL),
    (8,  2, 2, '2026-09-18', '2026-09-30'),
    (9,  6, 3, '2026-10-05', NULL),
    (10, 3, 1, '2026-10-08', '2026-10-15'),
    (11, 4, 4, '2026-10-10', '2026-10-20'),
    (12, 9, 1, '2026-10-12', NULL);

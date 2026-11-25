-- schema.sql
-- Creates the two tables and inserts fictional sample data.
-- db.py runs this file automatically ONLY if the tables do not exist yet.

CREATE TABLE departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE announcements (
    id         SERIAL PRIMARY KEY,
    title      VARCHAR(200) NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Sample data (all fictional)
INSERT INTO departments (name, description) VALUES
('Computer Science', 'Programming, algorithms, databases, networks and cloud computing. Includes modern labs for software development.'),
('Electrical Engineering', 'Electronics, power systems, signal processing and embedded systems with hands-on workshops.'),
('Business Administration', 'Management, accounting, marketing and entrepreneurship, with yearly company internships.'),
('Biology', 'Cell biology, genetics and ecology, with laboratory work and field trips in the Northvale region.'),
('Fine Arts', 'Drawing, painting, digital design and art history, with a student gallery open to the public.');

INSERT INTO announcements (title, content, created_at) VALUES
('Welcome to the new academic year', 'Classes at Northvale University start on Monday. Please check your timetable on the notice boards.', '2026-09-01 09:00'),
('Library opening hours extended', 'During the exam period the library will be open until 10 PM from Monday to Saturday.', '2026-10-05 14:30'),
('Career Fair next month', 'More than 30 companies will visit the main hall. Bring your CV and a student card.', '2026-10-20 11:00'),
('Winter exams schedule published', 'The exam schedule is now available at the administration office. Exams begin on January 12.', '2026-11-10 08:15');

CREATE TABLE email_list (
    email VARCHAR(255) NOT NULL,
    is_active NUMBER(1,0) DEFAULT 1,
    is_test_email NUMBER(1,0) DEFAULT 0,
    added_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    modified_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

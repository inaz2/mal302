CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    url VARCHAR(4098) NOT NULL,
    created TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE visitors (
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES urls (id),
    remote_addr VARCHAR(4098),
    remote_host VARCHAR(4098),
    user_agent VARCHAR(4098),
    referrer VARCHAR(4098),
    created TIMESTAMP DEFAULT current_timestamp
);

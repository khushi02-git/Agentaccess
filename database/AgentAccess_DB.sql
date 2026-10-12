CREATE DATABASE IF NOT EXISTS AgentAccess;
USE AgentAccess;

-- =========================
-- 1. ROLES
-- =========================
CREATE TABLE IF NOT EXISTS Roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- =========================
-- 2. PERMISSIONS
-- =========================
CREATE TABLE IF NOT EXISTS Permissions (
    permission_id INT PRIMARY KEY AUTO_INCREMENT,
    permission_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- =========================
-- 3. ROLE-PERMISSIONS
-- =========================
CREATE TABLE IF NOT EXISTS Role_Permissions (
    role_id INT,
    permission_id INT,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES Roles(role_id),
    FOREIGN KEY (permission_id) REFERENCES Permissions(permission_id)
);

-- =========================
-- 4. AGENTS
-- =========================
CREATE TABLE IF NOT EXISTS Agents (
    agent_id INT PRIMARY KEY AUTO_INCREMENT,
    agent_name VARCHAR(100) NOT NULL UNIQUE,
    role_id INT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES Roles(role_id)
);

-- =========================
-- 5. QUERY REQUESTS
-- =========================
CREATE TABLE IF NOT EXISTS Query_Requests (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    agent_id INT NOT NULL,
    query_text TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES Agents(agent_id)
);

-- =========================
-- 6. AUDIT LOGS
-- =========================
CREATE TABLE IF NOT EXISTS Audit_Logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    agent_id INT NOT NULL,
    request_id INT,
    action VARCHAR(50) NOT NULL,
    result VARCHAR(20) NOT NULL,
    details TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES Agents(agent_id),
    FOREIGN KEY (request_id) REFERENCES Query_Requests(request_id)
);

-- =========================
-- 7. EMPLOYEES
-- =========================
CREATE TABLE IF NOT EXISTS Employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    employee_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    salary DECIMAL(10,2)
);

-- =========================
-- 8. BLOCKED OPERATIONS
-- =========================
CREATE TABLE IF NOT EXISTS Blocked_Operations (
    operation_id INT PRIMARY KEY AUTO_INCREMENT,
    operation_name VARCHAR(50) NOT NULL UNIQUE,
    reason TEXT
);

-- =========================
-- INITIAL ROLES
-- =========================
INSERT IGNORE INTO Roles
(role_id, role_name, description) VALUES
(1, 'Admin', 'Full database access'),
(2, 'Analyst', 'Can read and update data'),
(3, 'ReadOnly', 'Can only read data');

-- =========================
-- INITIAL PERMISSIONS
-- =========================
INSERT IGNORE INTO Permissions
(permission_id, permission_name, description) VALUES
(1, 'SELECT', 'Read data'),
(2, 'INSERT', 'Insert new data'),
(3, 'UPDATE', 'Modify existing data'),
(4, 'DELETE', 'Delete data');

-- =========================
-- ROLE-PERMISSION MAPPING
-- =========================
INSERT IGNORE INTO Role_Permissions
(role_id, permission_id) VALUES
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(2, 1),
(2, 3),
(3, 1);

-- =========================
-- INITIAL AGENTS
-- =========================
INSERT IGNORE INTO Agents
(agent_id, agent_name, role_id) VALUES
(1, 'AdminAgent', 1),
(2, 'DataAgent', 2),
(3, 'ReportAgent', 3);

-- =========================
-- BLOCKED OPERATIONS
-- =========================
INSERT IGNORE INTO Blocked_Operations
(operation_name, reason) VALUES
('DROP', 'Dangerous database operation'),
('TRUNCATE', 'Dangerous database operation'),
('ALTER', 'Schema modification not allowed'),
('CREATE', 'Unauthorized schema modification'),
('GRANT', 'Permission modification not allowed'),
('REVOKE', 'Permission modification not allowed');
-- =========================
-- AGENT PERMISSIONS VIEW
-- =========================
CREATE OR REPLACE VIEW agent_permissions_view AS
SELECT
    a.agent_id,
    a.agent_name,
    r.role_id,
    r.role_name,
    p.permission_id,
    p.permission_name
FROM Agents a
JOIN Roles r
    ON a.role_id = r.role_id
JOIN Role_Permissions rp
    ON r.role_id = rp.role_id
JOIN Permissions p
    ON rp.permission_id = p.permission_id;
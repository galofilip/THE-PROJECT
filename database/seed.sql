-- B33 Seed Data
-- Test data for development and verification
-- Run after schema.sql

--------------------------------------------------------------
-- Sample private IP scans
--------------------------------------------------------------
INSERT INTO private_ip_scans (scan_id, target_ip, mac_address, hostname, open_ports, detected_services, vulnerabilities_found, network_ssid, network_bssid, risk_level, scan_source)
VALUES
    ('priv-scan-001', '192.168.1.1', 'AA:BB:CC:DD:EE:01', 'router.local', '[80, 443, 53]', '[{"port":80,"service":"nginx","version":"1.18.0"},{"port":443,"service":"nginx","version":"1.18.0"},{"port":53,"service":"dnsmasq","version":"2.85"}]', '[{"cve":"CVE-2021-23017","severity":"high","description":"nginx resolver vulnerability"}]', 'TestNetwork', 'AA:BB:CC:DD:EE:FF', 'high', 'pico'),

    ('priv-scan-002', '192.168.1.5', 'AA:BB:CC:DD:EE:05', 'desktop-pc', '[22, 80, 445, 3389]', '[{"port":22,"service":"OpenSSH","version":"7.4"},{"port":80,"service":"Apache","version":"2.4.49"},{"port":445,"service":"SMB","version":"3.0"},{"port":3389,"service":"RDP","version":"10.0"}]', '[{"cve":"CVE-2021-41773","severity":"critical","description":"Apache path traversal"},{"cve":"CVE-2017-0144","severity":"critical","description":"EternalBlue SMB vulnerability"}]', 'TestNetwork', 'AA:BB:CC:DD:EE:FF', 'critical', 'pico'),

    ('priv-scan-003', '192.168.1.10', 'AA:BB:CC:DD:EE:10', 'smart-tv', '[8080, 8443]', '[{"port":8080,"service":"HTTP","version":"unknown"},{"port":8443,"service":"HTTPS","version":"unknown"}]', '[]', 'TestNetwork', 'AA:BB:CC:DD:EE:FF', 'none', 'pico'),

    ('priv-scan-004', '192.168.1.20', 'AA:BB:CC:DD:EE:20', 'nas-server', '[22, 80, 443, 5000, 5001]', '[{"port":22,"service":"OpenSSH","version":"8.9"},{"port":80,"service":"nginx","version":"1.22.1"},{"port":5000,"service":"Synology DSM","version":"7.1"}]', '[{"cve":"CVE-2023-2729","severity":"medium","description":"Synology DSM information disclosure"}]', 'TestNetwork', 'AA:BB:CC:DD:EE:FF', 'medium', 'pico');

--------------------------------------------------------------
-- Sample public IP scans
--------------------------------------------------------------
INSERT INTO public_ip_scans (scan_id, target_ip, country_code, city, open_ports, detected_services, vulnerabilities_found, risk_level, scan_batch_id)
VALUES
    ('pub-scan-001', '203.0.113.10', 'IL', 'Tel Aviv', '[22, 80, 443]', '[{"port":22,"service":"OpenSSH","version":"8.2"},{"port":80,"service":"Apache","version":"2.4.41"},{"port":443,"service":"Apache","version":"2.4.41"}]', '[{"cve":"CVE-2021-44790","severity":"high","description":"Apache mod_lua buffer overflow"}]', 'high', 'batch-001'),

    ('pub-scan-002', '198.51.100.25', 'US', 'New York', '[80, 443, 8080]', '[{"port":80,"service":"nginx","version":"1.14.0"},{"port":443,"service":"nginx","version":"1.14.0"},{"port":8080,"service":"Tomcat","version":"9.0.30"}]', '[{"cve":"CVE-2020-1938","severity":"critical","description":"Apache Tomcat AJP Ghostcat"}]', 'critical', 'batch-001'),

    ('pub-scan-003', '192.0.2.50', 'IL', 'Haifa', '[22, 3306]', '[{"port":22,"service":"OpenSSH","version":"9.0"},{"port":3306,"service":"MySQL","version":"5.7.38"}]', '[{"cve":"CVE-2022-21417","severity":"medium","description":"MySQL Server optimizer vulnerability"}]', 'medium', 'batch-001');

--------------------------------------------------------------
-- Sample infected PCs
--------------------------------------------------------------
INSERT INTO infected_pcs (pc_id, hostname, username, internal_ip, external_ip, operating_system, architecture, backdoor_version, last_heartbeat, status, deployment_method, notes)
VALUES
    ('pc-001', 'DESKTOP-TEST01', 'testuser', '192.168.1.5', '203.0.113.50', 'Windows 11 Pro 10.0.26200', 'amd64', '1.0.0', datetime('now'), 'active', 'usb_hid', 'Test PC - authorized for testing'),

    ('pc-002', 'ubuntu-server', 'admin', '192.168.1.30', '203.0.113.51', 'Ubuntu 22.04 LTS', 'amd64', '1.0.0', datetime('now', '-2 hours'), 'active', 'exploit', 'Lab server - authorized');

--------------------------------------------------------------
-- Sample tasks in queue
--------------------------------------------------------------
INSERT INTO task_queue (task_id, task_type, target_ip, vulnerability_id, payload, status, assigned_to, result, error_message, completed_at)
VALUES
    ('task-001', 'scan_private', NULL, NULL, '{"network":"192.168.1.0/24","ports":"top100"}', 'completed', 'pico', '{"hosts_found":4,"vulnerabilities":5}', NULL, datetime('now', '-1 hour')),

    ('task-002', 'exploit', '192.168.1.5', 'CVE-2021-41773', '{"exploit_module":"apache_path_traversal","deploy_backdoor":true}', 'completed', 'pico', '{"success":true,"backdoor_deployed":true,"pc_id":"pc-001"}', NULL, datetime('now', '-30 minutes')),

    ('task-003', 'scan_public', NULL, NULL, '{"country":"IL","ip_count":100,"ports":"top50"}', 'in_progress', 'server', NULL, NULL, NULL),

    ('task-004', 'exploit', '192.168.1.20', 'CVE-2023-2729', '{"exploit_module":"synology_info_disclosure","deploy_backdoor":true}', 'pending', 'pico', NULL, NULL, NULL);

--------------------------------------------------------------
-- Sample exploitation logs
--------------------------------------------------------------
INSERT INTO exploitation_logs (task_id, target_ip, vulnerability_id, exploit_method, success, backdoor_deployed, pc_id, details, error_message)
VALUES
    ('task-002', '192.168.1.5', 'CVE-2021-41773', 'Apache path traversal + reverse shell', 1, 1, 'pc-001', '{"steps":["path traversal confirmed","uploaded payload","executed reverse shell","backdoor installed","persistence established"]}', NULL),

    (NULL, '192.168.1.1', 'CVE-2021-23017', 'nginx resolver exploit attempt', 0, 0, NULL, '{"steps":["exploit attempted","connection refused"]}', 'Target patched - exploit failed');

--------------------------------------------------------------
-- Sample C2 command logs
--------------------------------------------------------------
INSERT INTO c2_command_logs (pc_id, command_type, command_data, status, result, completed_at)
VALUES
    ('pc-001', 'shell', 'whoami', 'completed', 'testuser', datetime('now', '-20 minutes')),

    ('pc-001', 'shell', 'ipconfig /all', 'completed', 'Windows IP Configuration...', datetime('now', '-18 minutes')),

    ('pc-001', 'screenshot', NULL, 'completed', '{"filename":"screenshot_001.png","size_kb":245}', datetime('now', '-15 minutes')),

    ('pc-002', 'shell', 'uname -a', 'completed', 'Linux ubuntu-server 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux', datetime('now', '-10 minutes')),

    ('pc-002', 'upload', '{"local_path":"/tmp/tool.sh","remote_path":"C:\\temp\\tool.sh"}', 'sent', NULL, NULL);

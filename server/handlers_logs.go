package main

import (
	"net/http"
)

type LogHandler struct {
	DB *D1Client
}

// HandleExploitLogs handles GET /api/logs/exploits
func (h *LogHandler) HandleExploitLogs(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
		return
	}

	query := "SELECT * FROM exploitation_logs ORDER BY created_at DESC"
	params := []interface{}{}

	if targetIP := r.URL.Query().Get("target_ip"); targetIP != "" {
		query = "SELECT * FROM exploitation_logs WHERE target_ip = ?1 ORDER BY created_at DESC"
		params = append(params, targetIP)
	} else if success := r.URL.Query().Get("success"); success != "" {
		query = "SELECT * FROM exploitation_logs WHERE success = ?1 ORDER BY created_at DESC"
		params = append(params, success)
	}

	var logs []ExploitationLog
	if err := h.DB.QueryRows(&logs, query, params...); err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	if logs == nil {
		logs = []ExploitationLog{}
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: logs})
}

// HandleC2Logs handles GET /api/logs/c2
func (h *LogHandler) HandleC2Logs(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
		return
	}

	query := "SELECT * FROM c2_command_logs ORDER BY created_at DESC"
	params := []interface{}{}

	if pcID := r.URL.Query().Get("pc_id"); pcID != "" {
		query = "SELECT * FROM c2_command_logs WHERE pc_id = ?1 ORDER BY created_at DESC"
		params = append(params, pcID)
	} else if status := r.URL.Query().Get("status"); status != "" {
		query = "SELECT * FROM c2_command_logs WHERE status = ?1 ORDER BY created_at DESC"
		params = append(params, status)
	}

	var logs []C2CommandLog
	if err := h.DB.QueryRows(&logs, query, params...); err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	if logs == nil {
		logs = []C2CommandLog{}
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: logs})
}

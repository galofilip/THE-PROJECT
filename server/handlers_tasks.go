package main

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/google/uuid"
)

type TaskHandler struct {
	DB *D1Client
}

// HandleTasks routes GET/POST/PATCH for /api/tasks
func (h *TaskHandler) HandleTasks(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		h.listTasks(w, r)
	case http.MethodPost:
		h.createTask(w, r)
	case http.MethodPatch:
		h.updateTask(w, r)
	default:
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
	}
}

func (h *TaskHandler) listTasks(w http.ResponseWriter, r *http.Request) {
	query := "SELECT * FROM task_queue ORDER BY created_at DESC"
	params := []interface{}{}

	if status := r.URL.Query().Get("status"); status != "" {
		query = "SELECT * FROM task_queue WHERE status = ?1 ORDER BY created_at DESC"
		params = append(params, status)
	} else if assignedTo := r.URL.Query().Get("assigned_to"); assignedTo != "" {
		query = "SELECT * FROM task_queue WHERE assigned_to = ?1 ORDER BY created_at DESC"
		params = append(params, assignedTo)
	}

	var tasks []Task
	if err := h.DB.QueryRows(&tasks, query, params...); err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	if tasks == nil {
		tasks = []Task{}
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: tasks})
}

func (h *TaskHandler) createTask(w http.ResponseWriter, r *http.Request) {
	var req CreateTaskRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "invalid JSON body"})
		return
	}
	if req.TaskType == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "task_type is required"})
		return
	}

	taskID := uuid.New().String()
	assignedTo := req.AssignedTo
	if assignedTo == nil {
		defaultAssign := "pico"
		assignedTo = &defaultAssign
	}

	_, err := h.DB.Execute(
		`INSERT INTO task_queue (task_id, task_type, target_ip, vulnerability_id, payload, assigned_to)
		 VALUES (?1, ?2, ?3, ?4, ?5, ?6)`,
		taskID, req.TaskType, req.TargetIP, req.VulnerabilityID, req.Payload, assignedTo,
	)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}

	writeJSON(w, http.StatusCreated, APIResponse{Success: true, Data: map[string]string{"task_id": taskID}})
}

func (h *TaskHandler) updateTask(w http.ResponseWriter, r *http.Request) {
	// Extract task ID from path: /api/tasks/{id}
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/api/tasks"), "/")
	if len(parts) < 2 || parts[1] == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "task ID required in URL path"})
		return
	}
	taskID := parts[1]

	var req UpdateTaskRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "invalid JSON body"})
		return
	}

	// Build dynamic update query
	setClauses := []string{}
	params := []interface{}{}
	paramIdx := 1

	if req.Status != nil {
		setClauses = append(setClauses, "status = ?"+itoa(paramIdx))
		params = append(params, *req.Status)
		paramIdx++

		// Auto-set completed_at when marking as completed or failed
		if *req.Status == "completed" || *req.Status == "failed" {
			setClauses = append(setClauses, "completed_at = datetime('now')")
		}
	}
	if req.Result != nil {
		setClauses = append(setClauses, "result = ?"+itoa(paramIdx))
		params = append(params, *req.Result)
		paramIdx++
	}
	if req.ErrorMessage != nil {
		setClauses = append(setClauses, "error_message = ?"+itoa(paramIdx))
		params = append(params, *req.ErrorMessage)
		paramIdx++
	}

	if len(setClauses) == 0 {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "no fields to update"})
		return
	}

	sql := "UPDATE task_queue SET " + strings.Join(setClauses, ", ") + " WHERE task_id = ?" + itoa(paramIdx)
	params = append(params, taskID)

	_, err := h.DB.Execute(sql, params...)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}

	writeJSON(w, http.StatusOK, APIResponse{Success: true, Message: "task updated"})
}

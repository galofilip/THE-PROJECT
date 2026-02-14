package main

import (
	"encoding/json"
	"net/http"
)

type PicoHandler struct {
	DB *D1Client
}

// PicoPollResponse is what the Pico gets back when it polls.
type PicoPollResponse struct {
	Tasks []Task `json:"tasks"`
}

// PicoPollRequest allows the Pico to report task results while polling.
type PicoPollRequest struct {
	// Optional: report results for completed tasks
	CompletedTasks []PicoTaskResult `json:"completed_tasks,omitempty"`
}

type PicoTaskResult struct {
	TaskID       string  `json:"task_id"`
	Status       string  `json:"status"` // "completed" or "failed"
	Result       *string `json:"result"`
	ErrorMessage *string `json:"error_message"`
}

// HandlePoll handles POST /api/pico/poll
// Pico calls this every 30 seconds to:
// 1. Report any completed task results
// 2. Get new pending tasks assigned to "pico"
func (h *PicoHandler) HandlePoll(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
		return
	}

	// Parse optional completed task results
	var req PicoPollRequest
	if r.Body != nil && r.ContentLength > 0 {
		json.NewDecoder(r.Body).Decode(&req) // Ignore decode errors - body is optional
	}

	// Process completed tasks
	for _, result := range req.CompletedTasks {
		status := result.Status
		if status != "completed" && status != "failed" {
			continue
		}
		h.DB.Execute(
			`UPDATE task_queue SET status = ?1, result = ?2, error_message = ?3, completed_at = datetime('now')
			 WHERE task_id = ?4`,
			result.Status, result.Result, result.ErrorMessage, result.TaskID,
		)
	}

	// Get pending tasks for the Pico
	var tasks []Task
	err := h.DB.QueryRows(&tasks,
		`SELECT * FROM task_queue WHERE assigned_to = 'pico' AND status = 'pending' ORDER BY created_at ASC`,
	)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}

	// Mark returned tasks as "assigned"
	for _, task := range tasks {
		h.DB.Execute(
			`UPDATE task_queue SET status = 'assigned' WHERE task_id = ?1`,
			task.TaskID,
		)
	}

	if tasks == nil {
		tasks = []Task{}
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: PicoPollResponse{Tasks: tasks}})
}

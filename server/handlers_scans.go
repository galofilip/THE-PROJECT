package main

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/google/uuid"
)

type ScanHandler struct {
	DB *D1Client
}

// HandlePrivateScans routes GET/POST/DELETE for /api/scans/private
func (h *ScanHandler) HandlePrivateScans(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		h.listPrivateScans(w, r)
	case http.MethodPost:
		h.createPrivateScan(w, r)
	case http.MethodDelete:
		h.deletePrivateScan(w, r)
	default:
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
	}
}

func (h *ScanHandler) listPrivateScans(w http.ResponseWriter, r *http.Request) {
	query := "SELECT * FROM private_ip_scans ORDER BY created_at DESC"
	params := []interface{}{}

	// Optional filters
	if risk := r.URL.Query().Get("risk_level"); risk != "" {
		query = "SELECT * FROM private_ip_scans WHERE risk_level = ?1 ORDER BY created_at DESC"
		params = append(params, risk)
	} else if ssid := r.URL.Query().Get("network_ssid"); ssid != "" {
		query = "SELECT * FROM private_ip_scans WHERE network_ssid = ?1 ORDER BY created_at DESC"
		params = append(params, ssid)
	}

	var scans []PrivateIPScan
	if err := h.DB.QueryRows(&scans, query, params...); err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	if scans == nil {
		scans = []PrivateIPScan{}
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: scans})
}

func (h *ScanHandler) createPrivateScan(w http.ResponseWriter, r *http.Request) {
	var req CreatePrivateScanRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "invalid JSON body"})
		return
	}
	if req.TargetIP == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "target_ip is required"})
		return
	}

	scanID := uuid.New().String()
	_, err := h.DB.Execute(
		`INSERT INTO private_ip_scans (scan_id, target_ip, mac_address, hostname, open_ports, detected_services, vulnerabilities_found, network_ssid, network_bssid, risk_level, scan_source)
		 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)`,
		scanID, req.TargetIP, req.MACAddress, req.Hostname, req.OpenPorts, req.DetectedServices,
		req.VulnerabilitiesFound, req.NetworkSSID, req.NetworkBSSID, req.RiskLevel, req.ScanSource,
	)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}

	writeJSON(w, http.StatusCreated, APIResponse{Success: true, Data: map[string]string{"scan_id": scanID}})
}

func (h *ScanHandler) deletePrivateScan(w http.ResponseWriter, r *http.Request) {
	// Extract ID from path: /api/scans/private/{id}
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/api/scans/private"), "/")
	if len(parts) < 2 || parts[1] == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "scan ID required in URL path"})
		return
	}
	scanID := parts[1]

	_, err := h.DB.Execute("DELETE FROM private_ip_scans WHERE scan_id = ?1", scanID)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Message: "scan deleted"})
}

// HandlePublicScans routes GET/POST/DELETE for /api/scans/public
func (h *ScanHandler) HandlePublicScans(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		h.listPublicScans(w, r)
	case http.MethodPost:
		h.createPublicScan(w, r)
	case http.MethodDelete:
		h.deletePublicScan(w, r)
	default:
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "method not allowed"})
	}
}

func (h *ScanHandler) listPublicScans(w http.ResponseWriter, r *http.Request) {
	query := "SELECT * FROM public_ip_scans ORDER BY created_at DESC"
	params := []interface{}{}

	if risk := r.URL.Query().Get("risk_level"); risk != "" {
		query = "SELECT * FROM public_ip_scans WHERE risk_level = ?1 ORDER BY created_at DESC"
		params = append(params, risk)
	} else if country := r.URL.Query().Get("country_code"); country != "" {
		query = "SELECT * FROM public_ip_scans WHERE country_code = ?1 ORDER BY created_at DESC"
		params = append(params, country)
	} else if batch := r.URL.Query().Get("scan_batch_id"); batch != "" {
		query = "SELECT * FROM public_ip_scans WHERE scan_batch_id = ?1 ORDER BY created_at DESC"
		params = append(params, batch)
	}

	var scans []PublicIPScan
	if err := h.DB.QueryRows(&scans, query, params...); err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	if scans == nil {
		scans = []PublicIPScan{}
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: scans})
}

func (h *ScanHandler) createPublicScan(w http.ResponseWriter, r *http.Request) {
	var req CreatePublicScanRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "invalid JSON body"})
		return
	}
	if req.TargetIP == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "target_ip is required"})
		return
	}

	scanID := uuid.New().String()
	_, err := h.DB.Execute(
		`INSERT INTO public_ip_scans (scan_id, target_ip, country_code, city, open_ports, detected_services, vulnerabilities_found, risk_level, scan_batch_id)
		 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)`,
		scanID, req.TargetIP, req.CountryCode, req.City, req.OpenPorts, req.DetectedServices,
		req.VulnerabilitiesFound, req.RiskLevel, req.ScanBatchID,
	)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}

	writeJSON(w, http.StatusCreated, APIResponse{Success: true, Data: map[string]string{"scan_id": scanID}})
}

func (h *ScanHandler) deletePublicScan(w http.ResponseWriter, r *http.Request) {
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/api/scans/public"), "/")
	if len(parts) < 2 || parts[1] == "" {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: "scan ID required in URL path"})
		return
	}
	scanID := parts[1]

	_, err := h.DB.Execute("DELETE FROM public_ip_scans WHERE scan_id = ?1", scanID)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Message: "scan deleted"})
}

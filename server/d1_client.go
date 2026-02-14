package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

// D1Client handles all communication with Cloudflare D1 via REST API.
type D1Client struct {
	AccountID  string
	DatabaseID string
	APIToken   string
	HTTPClient *http.Client
}

func NewD1Client(accountID, databaseID, apiToken string) *D1Client {
	return &D1Client{
		AccountID:  accountID,
		DatabaseID: databaseID,
		APIToken:   apiToken,
		HTTPClient: &http.Client{},
	}
}

// d1QueryRequest is the JSON body sent to the D1 query endpoint.
type d1QueryRequest struct {
	SQL    string        `json:"sql"`
	Params []interface{} `json:"params,omitempty"`
}

// d1Response is the top-level response from the D1 API.
type d1Response struct {
	Result  []d1Result `json:"result"`
	Success bool       `json:"success"`
	Errors  []d1Error  `json:"errors"`
}

type d1Result struct {
	Results json.RawMessage `json:"results"`
	Success bool            `json:"success"`
	Meta    d1Meta          `json:"meta"`
}

type d1Meta struct {
	Duration    float64 `json:"duration"`
	Changes     int     `json:"changes"`
	LastRowID   int     `json:"last_row_id"`
	RowsRead    int     `json:"rows_read"`
	RowsWritten int     `json:"rows_written"`
}

type d1Error struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// Query executes a SQL query against D1 and returns the raw JSON results.
func (c *D1Client) Query(sql string, params ...interface{}) (json.RawMessage, error) {
	url := fmt.Sprintf(
		"https://api.cloudflare.com/client/v4/accounts/%s/d1/database/%s/query",
		c.AccountID, c.DatabaseID,
	)

	body := d1QueryRequest{SQL: sql, Params: params}
	bodyJSON, err := json.Marshal(body)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", url, bytes.NewReader(bodyJSON))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+c.APIToken)
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("http request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("D1 API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var d1Resp d1Response
	if err := json.Unmarshal(respBody, &d1Resp); err != nil {
		return nil, fmt.Errorf("unmarshal response: %w", err)
	}

	if !d1Resp.Success {
		if len(d1Resp.Errors) > 0 {
			return nil, fmt.Errorf("D1 error: %s", d1Resp.Errors[0].Message)
		}
		return nil, fmt.Errorf("D1 query failed")
	}

	if len(d1Resp.Result) == 0 {
		return json.RawMessage("[]"), nil
	}

	return d1Resp.Result[0].Results, nil
}

// QueryRows executes a SQL query and unmarshals the results into the provided slice.
func (c *D1Client) QueryRows(dest interface{}, sql string, params ...interface{}) error {
	raw, err := c.Query(sql, params...)
	if err != nil {
		return err
	}
	return json.Unmarshal(raw, dest)
}

// Execute runs a SQL statement (INSERT, UPDATE, DELETE) and returns the meta info.
func (c *D1Client) Execute(sql string, params ...interface{}) (*d1Meta, error) {
	url := fmt.Sprintf(
		"https://api.cloudflare.com/client/v4/accounts/%s/d1/database/%s/query",
		c.AccountID, c.DatabaseID,
	)

	body := d1QueryRequest{SQL: sql, Params: params}
	bodyJSON, err := json.Marshal(body)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", url, bytes.NewReader(bodyJSON))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+c.APIToken)
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("http request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("D1 API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var d1Resp d1Response
	if err := json.Unmarshal(respBody, &d1Resp); err != nil {
		return nil, fmt.Errorf("unmarshal response: %w", err)
	}

	if !d1Resp.Success {
		if len(d1Resp.Errors) > 0 {
			return nil, fmt.Errorf("D1 error: %s", d1Resp.Errors[0].Message)
		}
		return nil, fmt.Errorf("D1 execute failed")
	}

	if len(d1Resp.Result) == 0 {
		return &d1Meta{}, nil
	}

	return &d1Resp.Result[0].Meta, nil
}

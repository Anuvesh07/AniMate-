package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

type ClipService struct {
	baseURL string
	client  *http.Client
}

type ClipAnalysisRequest struct {
	ImageData string `json:"image_data"`
}

type ClipAnalysisResponse struct {
	Success     bool             `json:"success"`
	Character   *AnimeCharacter  `json:"character,omitempty"`
	Suggestions []AnimeCharacter `json:"suggestions,omitempty"`
	Error       string           `json:"error,omitempty"`
}

type AnimeCharacter struct {
	ID          int     `json:"id"`
	Name        string  `json:"name"`
	Anime       string  `json:"anime"`
	Description string  `json:"description"`
	ImageURL    string  `json:"image_url"`
	Confidence  float64 `json:"confidence"`
}

func NewClipService() *ClipService {
	baseURL := os.Getenv("CLIP_SERVICE_URL")
	if baseURL == "" {
		baseURL = "http://localhost:8001"
	}

	return &ClipService{
		baseURL: baseURL,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (cs *ClipService) AnalyzeImage(imageData string) (*ClipAnalysisResponse, error) {
	reqBody := ClipAnalysisRequest{
		ImageData: imageData,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}

	resp, err := cs.client.Post(
		cs.baseURL+"/analyze",
		"application/json",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to call CLIP service: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("CLIP service returned status %d", resp.StatusCode)
	}

	var result ClipAnalysisResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}

	return &result, nil
}

func (cs *ClipService) ReExamineImage(imageData string, excludeIDs []int, focusIDs []int, searchType string) (*ClipAnalysisResponse, error) {
	reqBody := map[string]interface{}{
		"image_data":  imageData,
		"exclude_ids": excludeIDs,
		"focus_ids":   focusIDs,
		"search_type": searchType,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}

	resp, err := cs.client.Post(
		cs.baseURL+"/re-examine",
		"application/json",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to call CLIP service: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("CLIP service returned status %d", resp.StatusCode)
	}

	var result ClipAnalysisResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}

	return &result, nil
}

func (cs *ClipService) RefreshDatabase() error {
	resp, err := cs.client.Post(cs.baseURL+"/refresh-database", "application/json", nil)
	if err != nil {
		return fmt.Errorf("failed to call refresh endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("refresh endpoint returned status %d", resp.StatusCode)
	}

	return nil
}

func (cs *ClipService) HealthCheck() (map[string]interface{}, error) {
	resp, err := cs.client.Get(cs.baseURL + "/health")
	if err != nil {
		return nil, fmt.Errorf("failed to call health endpoint: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("health endpoint returned status %d", resp.StatusCode)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode health response: %v", err)
	}

	return result, nil
}

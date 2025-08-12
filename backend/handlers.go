package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type AnalyzeRequest struct {
	ImageData string `json:"image_data" binding:"required"`
}

type ReExamineRequest struct {
	ImageData  string `json:"image_data" binding:"required"`
	ExcludeIDs []int  `json:"exclude_ids"`
	FocusIDs   []int  `json:"focus_ids"`
	SearchType string `json:"search_type"`
}

type AnalyzeResponse struct {
	Success     bool             `json:"success"`
	Character   *AnimeCharacter  `json:"character,omitempty"`
	Suggestions []AnimeCharacter `json:"suggestions,omitempty"`
	Error       string           `json:"error,omitempty"`
}

func AnalyzeImageHandler(clipService *ClipService) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req AnalyzeRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, AnalyzeResponse{
				Success: false,
				Error:   "Invalid request format",
			})
			return
		}

		// Analyze image with CLIP service
		result, err := clipService.AnalyzeImage(req.ImageData)
		if err != nil {
			c.JSON(http.StatusInternalServerError, AnalyzeResponse{
				Success: false,
				Error:   "Failed to analyze image: " + err.Error(),
			})
			return
		}

		c.JSON(http.StatusOK, result)
	}
}

func HealthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": "anime-guesser-api",
	})
}

func ReExamineImageHandler(clipService *ClipService) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req ReExamineRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, AnalyzeResponse{
				Success: false,
				Error:   "Invalid request format",
			})
			return
		}

		// Re-examine image with CLIP service
		result, err := clipService.ReExamineImage(req.ImageData, req.ExcludeIDs, req.FocusIDs, req.SearchType)
		if err != nil {
			c.JSON(http.StatusInternalServerError, AnalyzeResponse{
				Success: false,
				Error:   "Failed to re-examine image: " + err.Error(),
			})
			return
		}

		c.JSON(http.StatusOK, result)
	}
}

func RefreshDatabaseHandler(clipService *ClipService) gin.HandlerFunc {
	return func(c *gin.Context) {
		err := clipService.RefreshDatabase()
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"error":   err.Error(),
			})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"success": true,
			"message": "Database refresh initiated",
		})
	}
}

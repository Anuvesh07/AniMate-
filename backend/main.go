package main

import (
	"log"
	"os"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found")
	}

	// Initialize Gin router
	r := gin.Default()

	// Configure CORS
	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowHeaders = []string{"Origin", "Content-Length", "Content-Type", "Authorization"}
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	r.Use(cors.New(config))

	// Initialize services
	clipService := NewClipService()

	// Routes
	api := r.Group("/api")
	{
		api.POST("/analyze", AnalyzeImageHandler(clipService))
		api.POST("/re-examine", ReExamineImageHandler(clipService))
		api.GET("/health", HealthHandler)
		api.POST("/refresh-db", RefreshDatabaseHandler(clipService))
	}

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Server starting on port %s", port)
	log.Printf("CLIP service URL: %s", os.Getenv("CLIP_SERVICE_URL"))
	r.Run(":" + port)
}

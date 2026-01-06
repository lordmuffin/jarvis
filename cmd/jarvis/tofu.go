package main

import (
	"fmt"
	"os"
	"os/exec"

	"github.com/spf13/cobra"
)

var tofuCmd = &cobra.Command{
	Use:   "tofu [plan|apply]",
	Short: "Run OpenTofu commands via Jarvis Dagger engine",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		subcommand := args[0]
		
		// 1. Fetch secrets from 1Password for cloud providers
		// Note: This needs to be refined with actual secret retrieval logic
		// For now, we assume secrets are available or will be fetched here.
		// Example: jarvis-cli secret get aws-creds
		
		// Placeholder for detailed secret injection
		fmt.Println("Fetching secrets from 1Password...")
		// os.Setenv("AWS_ACCESS_KEY_ID", getSecret("op://vault/aws/access_key"))
		// os.Setenv("AWS_SECRET_ACCESS_KEY", getSecret("op://vault/aws/secret_key"))

		// 2. Execute Dagger call
		if subcommand == "plan" {
			executeDaggerTofu("plan")
		} else if subcommand == "apply" {
			executeDaggerTofu("apply")
		} else {
			fmt.Printf("Unknown subcommand: %s\n", subcommand)
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.AddCommand(tofuCmd)
}

func executeDaggerTofu(action string) {
	fmt.Printf("Executing Dagger Tofu %s...\n", action)
	
	// Construct the dagger call command
	// dagger call -m . tofu plan --source .
	// Note: We use -m . because the module is defined in dagger.json at root
	
	cmdArgs := []string{"call", "-m", ".", "tofu", action, "--source", "."}
	
	cmd := exec.Command("dagger", cmdArgs...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = os.Environ() // Pass through environment variables (including secrets)

	err := cmd.Run()
	if err != nil {
		fmt.Printf("Error running dagger command: %v\n", err)
		os.Exit(1)
	}
}

// Helper to simulate secret fetching (mock implementation)
func getSecret(ref string) string {
    // In a real implementation this would call 'op read ref'
    // For now we return empty or check env
    return "" 
}

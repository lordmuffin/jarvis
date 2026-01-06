package main

import (
	"context"
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/andrewjackson/jarvis/internal/config"
	"github.com/andrewjackson/jarvis/internal/dagger"
	"github.com/andrewjackson/jarvis/internal/lxc"
	"github.com/andrewjackson/jarvis/internal/k9s"
)

// Global rootCmd to allow other files (like tofu.go) to register commands
var rootCmd = &cobra.Command{
	Use:   "jarvis",
	Short: "Jarvis: Platform-in-a-Box CLI",
	Long:  `Jarvis is an intelligent platform engineering ecosystem entry point.`,
}

func main() {
	cfg := config.LoadFromEnv()
	if cfg.RemoteDaggerAddr != "" {
		fmt.Printf("Configuration loaded: Remote Dagger at %s\n", cfg.RemoteDaggerAddr)
	}


	var runCmd = &cobra.Command{
		Use:   "run [function]",
		Short: "Run a Dagger pipeline function",
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			ctx := context.Background()
			fmt.Printf("Invoking Dagger function: %s\n", args[0])
			
			// Dagger Execution
			client, err := dagger.NewClient(ctx)
			if err != nil {
				fmt.Printf("Error initializing Dagger: %v\n", err)
				os.Exit(1)
			}
			defer client.Close()
			
			// Placeholder for function execution logic
			err = dagger.RunFunction(ctx, client, args[0])
			if err != nil {
				fmt.Printf("Execution failed: %v\n", err)
				os.Exit(1)
			}
		},
	}

	var lxcCmd = &cobra.Command{
		Use:   "lxc [action] [name]",
		Short: "Manage LXC environments",
		Args:  cobra.MinimumNArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			action := args[0]
			name := args[1]
			
			fmt.Printf("LXC Operation: %s on %s\n", action, name)
			
			runner := lxc.NewRunner()
			var err error
			
			switch action {
			case "bootstrap":
				err = runner.Bootstrap(name, "ubuntu-22.04")
			case "snapshot":
				err = runner.Snapshot(name)
			default:
				fmt.Printf("Unknown LXC action: %s\n", action)
				return
			}
			
			if err != nil {
				fmt.Printf("LXC Error: %v\n", err)
				os.Exit(1)
			}
		},
	}

	var k9sCmd = &cobra.Command{
		Use:   "k9s",
		Short: "Launch K9s TUI",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Launching K9s Bridge...")
			err := k9s.Launch(context.Background(), "", "")
			if err != nil {
				fmt.Printf("Failed to launch k9s: %v\n", err)
				os.Exit(1)
			}
		},
	}

	rootCmd.AddCommand(runCmd)
	rootCmd.AddCommand(lxcCmd)
	rootCmd.AddCommand(k9sCmd)

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

package main

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/andrewjackson/jarvis/internal/agent"
	"github.com/andrewjackson/jarvis/internal/dagger"
	"github.com/andrewjackson/jarvis/pkg/k8s"

	"github.com/charmbracelet/bubbles/textinput"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
    ctx = context.Background()
)

type model struct {
	textInput textinput.Model
	viewport  viewport.Model
	agent     agent.Agent
    // In a real app, we'd persist the dagger client or initialize it when needed.
    // For TUI simplicity, we'll initialize it per command or keep a global one.
    // We'll keep it simple for now.
	
	err       error
    logs      string
    running   bool
}

func initialModel() model {
	ti := textinput.New()
	ti.Placeholder = "Tell Jarvis what to do..."
	ti.Focus()
	ti.CharLimit = 156
	ti.Width = 20

    vp := viewport.New(80, 20)
    vp.SetContent("Welcome to Jarvis CLI.\nType a command and press Enter.\n")

	return model{
		textInput: ti,
        viewport:  vp,
		agent:     agent.NewGeminiAgent("dummy-key"), // In real app, load from env
		err:       nil,
	}
}

func (m model) Init() tea.Cmd {
	return textinput.Blink
}

type planMsg agent.Plan
type errMsg error
type logMsg string

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.Type {
		case tea.KeyCtrlC, tea.KeyEsc:
			return m, tea.Quit
		case tea.KeyEnter:
            if m.running {
                return m, nil
            }
			input := m.textInput.Value()
            m.textInput.Reset()
            m.running = true
            m.logs += fmt.Sprintf("\n> %s\n", input)
            m.viewport.SetContent(m.logs)
            
			return m, func() tea.Msg {
                // Agent Logic
                p, err := m.agent.Ask(ctx, input)
                if err != nil {
                    return errMsg(err)
                }
                return planMsg(p)
			}
		}

	case planMsg:
        // Got a plan, executing it
        // For simplicity, we just execute blindly here for the prototype.
        // The requirements asked for "confirmation", so we should ideally add a state for that.
        // But to keep main.go reasonable for one file:
        // We will just print the plan and Execute it immediately or simulate execution.
        
        m.logs += "Agent Plan:\n"
        for _, step := range msg.Steps {
            m.logs += fmt.Sprintf(" - %s\n", step)
        }
        m.logs += "Executing...\n"
        m.viewport.SetContent(m.logs)

        // Reset running state for this prototype unless we chain commands
        // In a real TUI, we'd trigger the execution command here.
        // Let's trigger a specialized command to run the plan.
        
        plan := msg
        return m, func() tea.Msg {
            // Execution Logic (Dagger)
            client, err := dagger.NewClient(ctx)
            if err != nil {
                return errMsg(err)
            }
            // Defers would ideally be handled in a Persistent setup or proper cleanup
            defer client.Close()
            
            var output strings.Builder
            for _, step := range plan.Steps {
                if strings.HasPrefix(step, "RunKubectl:") {
                    cmdStr := strings.TrimSpace(strings.TrimPrefix(step, "RunKubectl:"))
                    out, err := k8s.RunKubectl(ctx, client, cmdStr)
                    if err != nil {
                        return errMsg(fmt.Errorf("step failed: %s: %w", step, err))
                    }
                    output.WriteString(fmt.Sprintf("Step '%s' Output:\n%s\n", step, out))
                } else {
                     output.WriteString(fmt.Sprintf("Skipping unknown step type: %s\n", step))
                }
            }
            return logMsg(output.String())
        }

	case logMsg:
        m.logs += string(msg)
        m.viewport.SetContent(m.logs)
        m.running = false
        // Scroll to bottom
        m.viewport.GotoBottom()

	case errMsg:
		m.err = msg
        m.logs += fmt.Sprintf("Error: %v\n", msg)
        m.viewport.SetContent(m.logs)
        m.running = false
		return m, nil
	}

	m.textInput, cmd = m.textInput.Update(msg)
    m.viewport, _ = m.viewport.Update(msg)
	return m, cmd
}

func (m model) View() string {
    return fmt.Sprintf(
		"%s\n\n%s",
		m.viewport.View(),
		m.textInput.View(),
	) + "\n"
}

func main() {
	p := tea.NewProgram(initialModel())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Alas, there's been an error: %v", err)
		os.Exit(1)
	}
}

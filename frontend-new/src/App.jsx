import { useState, useRef, useEffect } from 'react'
import { Code2, Brain, Terminal, Send, Loader2, Layers, ChevronRight, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, CheckCircle2, XCircle, Check, X } from 'lucide-react'
import MonacoEditor from '@monaco-editor/react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api'
const EMPTY_TESTS = []

// ─── Stack Problems Data ───────────────────────────────────────────────────────
const PROBLEMS = [
  {
    id: 1,
    slug: 'valid-parentheses',
    title: 'Valid Parentheses',
    difficulty: 'Easy',
    description:
      'Given a string s containing just the characters \'(\', \')\', \'{\', \'}\', \'[\' and \']\', determine if the input string is valid.\n\nA string is valid if:\n• Every open bracket is closed by the same type of bracket.\n• Open brackets are closed in the correct order.\n• Every close bracket has a corresponding open bracket.',
    examples: [
      { input: 's = "()"', output: 'True' },
      { input: 's = "()[]{}"', output: 'True' },
      { input: 's = "(]"', output: 'False' },
    ],
    starterCode: `def is_valid(s: str) -> bool:
    # Hint: use a stack to track open brackets
    pass
`,
  },
  {
    id: 2,
    slug: 'min-stack',
    title: 'Min Stack',
    difficulty: 'Medium',
    description:
      'Design a stack that supports push, pop, top, and retrieving the minimum element in constant time O(1).\n\nImplement the MinStack class:\n• MinStack() — initializes the stack object.\n• push(val) — pushes val onto the stack.\n• pop() — removes the top element.\n• top() — gets the top element.\n• getMin() — retrieves the minimum element.',
    examples: [
      { input: 'push(-2), push(0), push(-3)\ngetMin()', output: '-3' },
      { input: 'pop()\ntop()', output: '0' },
      { input: 'getMin()', output: '-2' },
    ],
    starterCode: `class MinStack:
    def __init__(self):
        # Hint: maintain a second stack for minimums
        pass

    def push(self, val: int) -> None:
        pass

    def pop(self) -> None:
        pass

    def top(self) -> int:
        pass

    def getMin(self) -> int:
        pass
`,
  },
  {
    id: 3,
    slug: 'daily-temperatures',
    title: 'Daily Temperatures',
    difficulty: 'Medium',
    description:
      'Given an array of integers temperatures representing daily temperatures, return an array answer such that answer[i] is the number of days you have to wait after the i-th day to get a warmer temperature.\n\nIf there is no future day with a warmer temperature, answer[i] = 0.',
    examples: [
      { input: 'temperatures = [73,74,75,71,69,72,76,73]', output: '[1,1,4,2,1,1,0,0]' },
      { input: 'temperatures = [30,40,50,60]', output: '[1,1,1,0]' },
      { input: 'temperatures = [30,60,90]', output: '[1,1,0]' },
    ],
    starterCode: `def daily_temperatures(temperatures: list[int]) -> list[int]:
    # Hint: use a monotonic decreasing stack of indices
    pass
`,
  },
  {
    id: 4,
    slug: 'evaluate-rpn',
    title: 'Evaluate Reverse Polish Notation',
    difficulty: 'Medium',
    description:
      'Evaluate the value of an arithmetic expression in Reverse Polish Notation (RPN).\n\nValid operators are +, -, *, and /. Each operand may be an integer or another expression.\n\nNote: Division truncates toward zero.',
    examples: [
      { input: 'tokens = ["2","1","+","3","*"]', output: '9' },
      { input: 'tokens = ["4","13","5","/","+"]', output: '6' },
      { input: 'tokens = ["10","6","9","3","+","-11","*","/","*","17","+","5","+"]', output: '22' },
    ],
    starterCode: `def eval_rpn(tokens: list[str]) -> int:
    # Hint: push operands; on operator, pop two values and push result
    pass
`,
  },
]

const DIFF_COLORS = {
  Easy:   'text-[#667085]',
  Medium: 'text-[#667085]',
  Hard:   'text-[#667085]',
}

// ─── Problem Sidebar ───────────────────────────────────────────────────────────
function ProblemSidebar({ problems, selected, onSelect, isCollapsed, onToggle }) {
  if (isCollapsed) {
    return (
      <div className="flex h-full w-12 shrink-0 flex-col items-center border-r border-[#313244] bg-[#181825]">
        <button
          onClick={onToggle}
          className="mt-3 inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[#313244] bg-[#1e1e2e] text-[#cdd6f4] transition-colors hover:bg-[#232334]"
          aria-label="Show problems panel"
          title="Show problems panel"
        >
          <PanelLeftOpen size={14} />
        </button>
        <span className="mt-3 -rotate-90 whitespace-nowrap text-[10px] font-semibold uppercase tracking-widest text-[#585b70]">
          Problems
        </span>
      </div>
    )
  }

  return (
    <div className="flex flex-col w-56 shrink-0 h-full bg-[#181825] border-r border-[#313244]">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-[#313244]">
        <Layers size={15} className="text-[#89b4fa]" />
        <span className="text-xs font-semibold text-[#cdd6f4] tracking-widest uppercase">Problems</span>
        <button
          onClick={onToggle}
          className="ml-auto inline-flex h-7 w-7 items-center justify-center rounded-md border border-[#313244] bg-[#1e1e2e] text-[#cdd6f4] transition-colors hover:bg-[#232334]"
          aria-label="Hide problems panel"
          title="Hide problems panel"
        >
          <PanelLeftClose size={13} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {problems.map((p) => (
          <button
            key={p.id}
            onClick={() => onSelect(p)}
            className={`w-full text-left px-4 py-3 border-b border-[#1e1e2e] transition-colors cursor-pointer ${
              selected?.id === p.id
                ? 'bg-[#dbeafe]'
                : 'hover:bg-[#232334]'
            }`}
          >
            <div className="flex items-center justify-between gap-1">
              <span className="text-xs font-medium text-[#cdd6f4] leading-snug">{p.title}</span>
              {selected?.id === p.id && <ChevronRight size={12} className="text-[#89b4fa] shrink-0" />}
            </div>
            <span className={`text-xs mt-1 block font-semibold ${DIFF_COLORS[p.difficulty]}`}>
              {p.difficulty}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── Problem Description Panel ─────────────────────────────────────────────────
function ProblemPane({ problem }) {
  if (!problem) return null
  return (
    <div className="overflow-y-auto h-full px-5 py-4 space-y-4 text-sm text-[#cdd6f4]">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <h2 className="font-bold text-[#cdd6f4] text-base">{problem.title}</h2>
          <span className={`text-xs font-semibold ${DIFF_COLORS[problem.difficulty]}`}>
            {problem.difficulty}
          </span>
        </div>
        <p className="text-[#a6adc8] leading-relaxed whitespace-pre-wrap">{problem.description}</p>
      </div>
      <div className="space-y-2">
        {problem.examples.map((ex, i) => (
          <div key={i} className="rounded-lg bg-[#11111b] border border-[#313244] p-3 font-mono text-xs space-y-1">
            <div><span className="text-[#585b70]">Input:  </span><span className="text-[#a6e3a1]">{ex.input}</span></div>
            <div><span className="text-[#585b70]">Output: </span><span className="text-[#89b4fa]">{ex.output}</span></div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Test Results Panel ───────────────────────────────────────────────────────
function TestResultsPanel({ testResults }) {
  const [selectedIdx, setSelectedIdx] = useState(0)
  const tests = testResults?.tests || EMPTY_TESTS

  if (!testResults) return null

  const { passed, total, failed, status, reason } = testResults

  const selectedTest = tests[selectedIdx] || tests[0]
  const isAllPassed = status === 'passed' && failed === 0

  return (
    <div className="flex flex-col border-t border-[#313244] bg-[#181825] h-52 shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#313244] bg-[#11111b]">
        <div className="flex items-center gap-2">
          {isAllPassed ? (
            <CheckCircle2 size={16} className="text-[#a6e3a1]" />
          ) : (
            <XCircle size={16} className="text-[#f38ba8]" />
          )}
          <span className="text-xs font-bold uppercase tracking-wider text-[#cdd6f4]">
            Tests
          </span>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-bold ${
              isAllPassed
                ? 'bg-[#a6e3a1]/20 text-[#a6e3a1] border border-[#a6e3a1]/40'
                : 'bg-[#f38ba8]/20 text-[#f38ba8] border border-[#f38ba8]/40'
            }`}
          >
            {passed} / {total} passed
          </span>
        </div>

        {reason === 'syntax_error' && (
          <span className="text-xs text-[#f38ba8] font-mono font-semibold">
            Syntax Error
          </span>
        )}
        {reason === 'runtime_error' && (
          <span className="text-xs text-[#f38ba8] font-mono font-semibold">
            Runtime Error
          </span>
        )}
      </div>

      {/* Test Tabs */}
      <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-[#313244]/60 bg-[#181825] overflow-x-auto">
        {tests.map((t, idx) => {
          const isSelected = idx === selectedIdx
          return (
            <button
              key={t.test_id}
              onClick={() => setSelectedIdx(idx)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors cursor-pointer ${
                isSelected
                  ? 'bg-[#313244] text-[#cdd6f4] ring-1 ring-[#89b4fa]'
                  : 'bg-[#1e1e2e] text-[#a6adc8] hover:bg-[#232334]'
              }`}
            >
              {t.passed ? (
                <Check size={12} className="text-[#a6e3a1]" />
              ) : (
                <X size={12} className="text-[#f38ba8]" />
              )}
              <span>Test {t.test_id}</span>
            </button>
          )
        })}
      </div>

      {/* Selected Test Body */}
      {selectedTest && (
        <div className="flex-1 overflow-y-auto px-4 py-2.5 font-mono text-xs space-y-2 bg-[#181825]">
          {selectedTest.error ? (
            <div className="rounded border border-[#f38ba8]/30 bg-[#f38ba8]/10 p-2 text-[#f38ba8] whitespace-pre-wrap">
              <span className="font-bold">Error: </span>
              {selectedTest.error}
            </div>
          ) : null}

          <div className="grid grid-cols-1 gap-1.5">
            <div>
              <span className="text-[#585b70] font-semibold">Input: </span>
              <span className="text-[#cdd6f4] bg-[#11111b] px-1.5 py-0.5 rounded border border-[#313244]">
                {typeof selectedTest.input === 'string'
                  ? `"${selectedTest.input}"`
                  : JSON.stringify(selectedTest.input)}
              </span>
            </div>
            <div>
              <span className="text-[#585b70] font-semibold">Expected: </span>
              <span className="text-[#a6e3a1] bg-[#11111b] px-1.5 py-0.5 rounded border border-[#313244]">
                {String(selectedTest.expected)}
              </span>
            </div>
            <div>
              <span className="text-[#585b70] font-semibold">Actual: </span>
              <span
                className={`px-1.5 py-0.5 rounded border border-[#313244] bg-[#11111b] ${
                  selectedTest.passed ? 'text-[#a6e3a1]' : 'text-[#f38ba8]'
                }`}
              >
                {selectedTest.actual !== null ? String(selectedTest.actual) : 'null'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Left Panel — Code Editor ─────────────────────────────────────────────────
function CodeEditorPanel({ problem, code, language, setCode, isLoading, onSubmit, testResults }) {
  return (
    <div className="flex h-full min-w-0 flex-1 border-r border-[#313244]">
      {/* Problem description — left strip */}
      <div className="flex flex-col w-[42%] min-w-[280px] h-full border-r border-[#313244] bg-[#1e1e2e]">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-[#313244] bg-[#181825] shrink-0">
          <Code2 size={16} className="text-[#89b4fa]" />
          <span className="text-xs font-semibold text-[#cdd6f4] tracking-wide">Problem</span>
        </div>
        <div className="flex-1 overflow-hidden">
          <ProblemPane problem={problem} />
        </div>
      </div>

      {/* Editor — right strip */}
      <div className="flex min-w-0 flex-col flex-1 h-full bg-[#1e1e2e]">
        {/* Header */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-[#313244] bg-[#181825] shrink-0">
          <Code2 size={18} className="text-[#89b4fa]" />
          <span className="text-sm font-semibold text-[#cdd6f4] tracking-wide">Code Editor</span>
          <div className="ml-auto flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#d9dee7]" />
            <span className="w-3 h-3 rounded-full bg-[#d9dee7]" />
            <span className="w-3 h-3 rounded-full bg-[#d9dee7]" />
          </div>
        </div>

        {/* Monaco Editor */}
        <div className="flex-1 min-w-0 overflow-hidden">
          <MonacoEditor
            height="100%"
            language={language}
            theme="vs-light"
            value={code}
            onChange={(val) => setCode(val ?? '')}
            options={{
              fontSize: 14,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: 'on',
              renderLineHighlight: 'line',
              padding: { top: 16, bottom: 16 },
              fontFamily: "'Fira Code', 'JetBrains Mono', monospace",
              fontLigatures: true,
            }}
          />
        </div>

        {/* Test Results */}
        <TestResultsPanel testResults={testResults} />

        {/* Footer — Submit */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-[#313244] bg-[#181825] shrink-0">
          <div className="flex gap-2 text-xs text-[#585b70]">
            <span className="px-2 py-1 rounded bg-[#313244] text-[#a6e3a1]">Python 3</span>
            <span className="px-2 py-1 rounded bg-[#313244]">
              {isLoading ? 'Running…' : 'Ready'}
            </span>
          </div>
          <button
            onClick={onSubmit}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#89b4fa] hover:bg-[#74c7ec] text-white text-sm font-semibold transition-colors duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <><Loader2 size={14} className="animate-spin" />Analyzing…</>
            ) : (
              <><Send size={14} />Submit</>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Top-Right Panel — Socratic Tutor ────────────────────────────────────────
function TutorPanel({ chatHistory, chatInput, setChatInput, onSendChat, isChatLoading, isCollapsed, onToggle, embedded = false, hideHeader = false }) {
  const endRef = useRef(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  if (isCollapsed) {
    return (
      <div className="flex h-[70%] items-start justify-center border-b border-[#313244] bg-[#181825] py-3">
        <button
          onClick={onToggle}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[#313244] bg-[#1e1e2e] text-[#cdd6f4] transition-colors hover:bg-[#232334]"
          aria-label="Show tutor panel"
          title="Show tutor panel"
        >
          <PanelRightOpen size={14} />
        </button>
      </div>
    )
  }

  return (
    <div className={`flex min-h-0 flex-col ${embedded ? 'flex-1' : 'h-[58%]'} border-b border-[#313244]`}>
      {/* Header */}
      {!hideHeader && <div className="flex items-center gap-2 px-4 py-3 border-b border-[#313244] bg-[#181825]">
        <Brain size={18} className="text-[#cba6f7]" />
        <span className="text-sm font-semibold text-[#cdd6f4] tracking-wide">
          Socratic Tutor
        </span>
        <span className="ml-auto flex items-center gap-1.5 text-xs text-[#a6e3a1]">
          <span className="w-2 h-2 rounded-full bg-[#a6e3a1] animate-pulse" />
          Active
        </span>
        <button
          onClick={onToggle}
          className="ml-2 inline-flex h-7 w-7 items-center justify-center rounded-md border border-[#313244] bg-[#1e1e2e] text-[#cdd6f4] transition-colors hover:bg-[#232334]"
          aria-label="Hide tutor panel"
          title="Hide tutor panel"
        >
          <PanelRightClose size={13} />
        </button>
      </div>}

      {/* Scrollable messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {chatHistory.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#dbeafe] text-[#111827] rounded-tr-sm'
                  : 'bg-[#f2f4f7] text-[#111827] rounded-tl-sm'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* Input row */}
      <div className="flex items-center gap-2 px-4 py-3 border-t border-[#313244] bg-[#181825]">
        <input
          type="text"
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && onSendChat()}
          placeholder="Ask a question or explain your approach…"
          className="flex-1 bg-white text-[#111827] placeholder-[#585b70] text-sm rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-[#89b4fa] transition border border-[#d9dee7]"
          disabled={isChatLoading}
        />
        <button
          onClick={onSendChat}
          disabled={isChatLoading || !chatInput.trim()}
          className="p-2 rounded-lg bg-[#cba6f7] hover:bg-[#b4befe] text-white transition-colors duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isChatLoading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
        </button>
      </div>
    </div>
  )
}

function EvaluationTab({ agentLogs, misconception, testResults }) {
  const execution = testResults?.execution
  const passed = testResults ? `${testResults.passed} / ${testResults.total} tests passed` : 'No submission yet'
  const agentCards = ['CRITIC', 'DEFENDER', 'JUDGE'].map((role) => ({
    role,
    message: agentLogs.find((line) => line.startsWith(`[${role}]`))?.replace(`[${role}] `, '') || 'No analysis yet.',
  }))
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded border border-[#d9dee7] bg-white p-2"><div className="text-[#667085]">Submission</div><div className="mt-1 font-semibold text-[#16a34a]">Received</div></div>
        <div className="rounded border border-[#d9dee7] bg-white p-2"><div className="text-[#667085]">Tests</div><div className="mt-1 font-semibold">{passed}</div></div>
        <div className="rounded border border-[#d9dee7] bg-white p-2"><div className="text-[#667085]">Runtime</div><div className="mt-1 font-semibold">{execution?.success ? 'Passed' : execution ? 'Failed' : 'Pending'}</div></div>
      </div>
      <div className="rounded border border-[#d9dee7] bg-white p-3"><div className="font-semibold">Execution</div><div className="mt-1 font-mono text-[#7f1d1d]">{execution?.stderr || testResults?.reason || 'Awaiting submission'}</div></div>
      <div className="rounded border border-[#d9dee7] bg-white p-3"><div className="mb-2 font-semibold">Evaluation flow</div><div className="flex flex-wrap items-center gap-1 text-[#667085]"><span>Submission</span><span>→</span><span>Execution</span><span>→</span><span>Critic + Defender</span><span>→</span><span>Judge</span><span>→</span><span className="text-[#d97706]">{misconception?.id || 'Pending'}</span></div></div>
      <div className="border-t border-[#d9dee7] pt-3"><div className="mb-2 font-semibold">Agent summary</div><div className="grid gap-2">{agentCards.map(({ role, message }) => <div key={role} className="rounded border border-[#d9dee7] bg-white p-3"><div className="font-bold text-[#2563eb]">{role}</div><div className="mt-2 leading-5 text-[#111827]">{message}</div></div>)}</div></div>
    </div>
  )
}

function AgentsTab({ agentLogs }) {
  return <div className="flex-1 overflow-y-auto p-4 text-xs"><div className="mb-3 flex items-center justify-between"><span className="font-semibold">Multi-agent evaluation</span><span className="text-[#16a34a]">{agentLogs.length > 2 ? 'Completed' : 'Waiting'}</span></div><div className="space-y-2">{['CRITIC', 'DEFENDER', 'JUDGE'].map((role) => { const log = agentLogs.find((line) => line.startsWith(`[${role}]`)); return <div key={role} className="rounded border border-[#d9dee7] bg-white p-3"><div className="font-bold text-[#2563eb]">{role}</div><div className="mt-2 leading-5 text-[#111827]">{log?.replace(`[${role}] `, '') || 'No analysis yet.'}</div></div> })}</div><div className="mt-4 rounded border border-[#d9dee7] bg-white p-3 text-center text-[#667085]">Submission → Critic + Defender → Judge</div></div>
}

function LearningTab({ misconception, recurrenceCount, sameStreak, agentLogs }) {
  const [attempts, setAttempts] = useState([])
  useEffect(() => {
    if (!misconception?.id) return
    const attemptsUrl = `${API_BASE}/attempts/test-user-1/${encodeURIComponent(misconception.id)}`
    console.log('[LearningTab] fetching attempts:', attemptsUrl)
    axios.get(attemptsUrl)
      .then((response) => {
        console.log('[LearningTab] attempts response:', { status: response.status, body: response.data })
        setAttempts(response.data)
      })
      .catch(() => setAttempts([]))
  }, [misconception?.id, recurrenceCount])
  const judge = agentLogs.find((line) => line.startsWith('[JUDGE]'))
  const feedbackLabel = sameStreak ? `${recurrenceCount}x recurrence` : 'Current attempt'
  const displayedAttempts = misconception?.id ? attempts : []
  return <div className="flex-1 overflow-y-auto p-4 text-xs"><div className="rounded border border-[#fcd34d] bg-[#fffbeb] p-3"><div className="font-semibold text-[#d97706]">Learning insights</div><div className="mt-2 text-sm font-semibold text-[#111827]">{misconception?.id ? misconception.id.replace(/-/g, ' ') : 'No misconception detected'}</div><div className="mt-1 font-mono text-[#92400e]">{misconception?.id || 'Awaiting submission'}</div><div className="mt-2 leading-5 text-[#667085]">Evidence line: {misconception?.evidence_line || 'N/A'}</div><div className="mt-2 text-[#d97706]">Model confidence: {misconception ? `${Math.round(misconception.confidence * 100)}%` : 'N/A'}</div></div><div className="mt-4 font-semibold">Recent attempts</div><div className="mt-2 space-y-2">{displayedAttempts.map((attempt, index) => <div key={attempt.id} className="flex items-center justify-between rounded border border-[#d9dee7] bg-white px-3 py-2"><span className="font-medium">Attempt {displayedAttempts.length - index}</span><span className="text-[#667085]">{misconception.id} · {index === 0 ? 'Current' : 'Repeated'}</span><span className="text-[#2563eb]">{Math.round(attempt.confidence * 100)}% confidence</span></div>)}</div><div className="mt-4 rounded border border-[#bfdbfe] bg-[#eff6ff] p-3"><div className="font-semibold text-[#2563eb]">Adaptive feedback · {feedbackLabel}</div><div className="mt-2 leading-5 text-[#1e3a8a]">{judge?.replace('[JUDGE] ', '') || 'Submit code to receive adaptive feedback.'}</div></div></div>
}

function IntelligencePanel({ chatHistory, chatInput, setChatInput, onSendChat, isChatLoading, terminalCollapsed, agentLogs, misconception, recurrenceCount, sameStreak, testResults }) {
  const [tab, setTab] = useState('Tutor')
  return <div className={`flex min-h-0 flex-col border-b border-[#313244] bg-[#f5f7fa] ${terminalCollapsed ? 'flex-1' : 'h-[58%]'}`}>
    <div className="flex shrink-0 items-center gap-1 border-b border-[#d9dee7] bg-white px-3 py-2">
      {['Tutor', 'Evaluation', 'Agents', 'Learning'].map((item) => <button key={item} onClick={() => setTab(item)} className={`border-b-2 px-2 py-1.5 text-xs font-semibold ${tab === item ? 'border-[#2563eb] text-[#2563eb]' : 'border-transparent text-[#667085]'}`}>{item}</button>)}
    </div>
    {tab === 'Tutor' && <TutorPanel chatHistory={chatHistory} chatInput={chatInput} setChatInput={setChatInput} onSendChat={onSendChat} isChatLoading={isChatLoading} isCollapsed={false} onToggle={() => {}} embedded hideHeader />}
    {tab === 'Evaluation' && <EvaluationTab agentLogs={agentLogs} misconception={misconception} testResults={testResults} />}
    {tab === 'Agents' && <AgentsTab agentLogs={agentLogs} />}
    {tab === 'Learning' && <LearningTab misconception={misconception} recurrenceCount={recurrenceCount} sameStreak={sameStreak} agentLogs={agentLogs} />}
  </div>
}

// ─── Bottom-Right Panel — Agent Terminal ──────────────────────────────────────
function AgentTerminal({ agentLogs, misconception, recurrenceCount, isCollapsed, onToggle }) {
  const endRef = useRef(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [agentLogs, misconception])

  if (isCollapsed) {
    return (
      <div className="flex h-12 shrink-0 items-start justify-center border-t border-[#313244] bg-[#11111b] py-2">
        <button
          onClick={onToggle}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[#313244] bg-[#1e1e2e] text-[#a6e3a1] transition-colors hover:bg-[#232334]"
          aria-label="Show terminal panel"
          title="Show terminal panel"
        >
          <PanelRightOpen size={14} />
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[42%] bg-[#11111b]">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-[#313244] bg-[#181825]">
        <Terminal size={16} className="text-[#a6e3a1]" />
        <span className="text-xs font-semibold text-[#a6e3a1] tracking-widest uppercase">
          Agent Terminal
        </span>
        <button
          onClick={onToggle}
          className="ml-auto inline-flex h-7 w-7 items-center justify-center rounded-md border border-[#313244] bg-[#181825] text-[#a6e3a1] transition-colors hover:bg-[#232334]"
          aria-label="Hide terminal panel"
          title="Hide terminal panel"
        >
          <PanelRightClose size={13} />
        </button>
      </div>

      {/* Log output */}
      <div className="flex-1 overflow-y-auto px-4 py-3 font-mono text-xs text-[#111827] space-y-1 leading-5">
        {agentLogs.map((line, i) => (
          <div key={i} className={line.endsWith('_') ? 'animate-pulse' : ''}>
            {line}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* Misconception block — pinned, only when id is present */}
      {misconception?.id && (
        <div className="shrink-0 mx-4 mb-2 rounded-lg border border-[#f38ba8]/40 bg-[#f38ba8]/10 px-3 py-1.5 flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="text-[#585b70] text-xs font-semibold uppercase tracking-wider">Misconception</span>
          <span className="text-[#f38ba8] text-xs font-semibold">
            &ldquo;{misconception.id.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}&rdquo;
          </span>
          <span className="text-[#a6adc8] text-xs">{Math.round(misconception.confidence * 100)}% conf</span>
          <span className="text-[#a6adc8] text-xs">line {misconception.evidence_line}</span>
          {recurrenceCount > 1 && (
            <span className="px-2 py-0.5 rounded-full bg-[#f9e2af]/20 text-[#f9e2af] text-xs font-semibold border border-[#f9e2af]/40">
              {recurrenceCount}x recurrence
            </span>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Root App ─────────────────────────────────────────────────────────────────
function App() {
  const [selectedProblem, setSelectedProblem] = useState(PROBLEMS[0])
  const [code, setCode] = useState(PROBLEMS[0].starterCode)
  const [language] = useState('python')
  const [isLoading, setIsLoading] = useState(false)
  const [isProblemsCollapsed, setIsProblemsCollapsed] = useState(false)
  const [isTutorCollapsed, setIsTutorCollapsed] = useState(false)
  const [isTerminalCollapsed, setIsTerminalCollapsed] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [chatHistory, setChatHistory] = useState([
    {
      role: 'bot',
      content: "Hello! I'm your Socratic Tutor. Pick a problem, write your solution, and hit Submit!",
    },
  ])
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [agentLogs, setAgentLogs] = useState([
    '> System ready. Awaiting code submission…',
    '> _',
  ])
  const [testResults, setTestResults] = useState(null)
  const [misconception, setMisconception] = useState(null)   // full object
  const [recurrenceCount, setRecurrenceCount] = useState(0)
  const [sameStreak, setSameStreak] = useState(false)
  const miscHistory = useRef([])  // frontend-side recurrence tracker

  const handleSendChat = async () => {
    const text = chatInput.trim()
    if (!text || isChatLoading) return

    const userMsg = { role: 'user', content: text }
    const updatedHistory = [...chatHistory, userMsg]
    setChatHistory(updatedHistory)
    setChatInput('')
    setIsChatLoading(true)

        try {
      const response = await axios.post(`${API_BASE}/chat`, {
        messages: updatedHistory.map((m) => ({
          role: m.role === 'bot' ? 'assistant' : m.role,
          content: m.content,
        })),
      })
      setChatHistory((prev) => [
        ...prev,
        { role: 'bot', content: response.data.reply },
      ])
    } catch (err) {
      const msg = err.response?.data?.detail ?? err.message ?? 'Unknown error.'
      setChatHistory((prev) => [
        ...prev,
        { role: 'bot', content: `⚠️ Error: ${msg}` },
      ])
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleSelectProblem = (problem) => {
    setSelectedProblem(problem)
    setCode(problem.starterCode)
    setTestResults(null)
    setChatHistory([
      {
        role: 'bot',
        content: `Let's tackle **${problem.title}**! Read the problem description, write your solution, then hit Submit.`,
      },
    ])
    setAgentLogs([
      `> Problem loaded: ${problem.title} [${problem.difficulty}]`,
      '> Awaiting code submission…',
      '> _',
    ])
    setMisconception(null)
    setRecurrenceCount(0)
    setSameStreak(false)
    miscHistory.current = []
  }

  const handleSubmitCode = async () => {
    setIsLoading(true)
    setChatHistory((prev) => [
      ...prev,
      { role: 'user', content: 'Submitted code for evaluation...' },
    ])
    setAgentLogs((prev) => [
      ...prev.filter((l) => !l.endsWith('_')),
      '> [orchestrator] Received submission. Routing to agents…',
      '> _',
    ])

    try {
      const response = await axios.post(`${API_BASE}/submit`, {
        user_id: 'test-user-1',
        problem_id: selectedProblem.slug,
        code,
      })
      const data = response.data

      if (data.test_results) {
        setTestResults(data.test_results)
      }

      // Build agent log lines from contract fields: critic, defender, judge
      const logs = []
      if (data.critic)   logs.push(`[CRITIC] ${data.critic}`)
      if (data.defender) logs.push(`[DEFENDER] ${data.defender}`)
      if (data.judge)    logs.push(`[JUDGE] ${data.judge}`)
      // Fallback: legacy agent_logs array if backend still returns old shape
      const agentLines = logs.length > 0 ? logs : (() => {
        const lines = Array.isArray(data.agent_logs) ? [...data.agent_logs] : []
        // Replace hardcoded Judge placeholder with actual tutor_response
        const judgeIdx = lines.reduce((last, l, i) => l.startsWith('[JUDGE]') ? i : last, -1)
        if (judgeIdx !== -1 && data.tutor_response)
          lines[judgeIdx] = `[JUDGE] ${data.tutor_response}`
        return lines
      })()

      if (agentLines.length > 0) {
        setAgentLogs([...agentLines, '> _'])
      }
      // Judge hint — contract: data.judge, legacy fallback: data.tutor_response
      const hint = data.judge ?? data.tutor_response
      if (hint) {
        setChatHistory((prev) => [
          ...prev,
          { role: 'bot', content: hint },
        ])
      }
      // Misconception — always set after submission; use fallback if id missing
      const mid = data.misconception?.id || 'unclassified-misconception'
      const conf = typeof data.misconception?.confidence === 'number' ? data.misconception.confidence : 0.5
      const evLine = data.misconception?.evidence_line ?? 1
      setMisconception({ id: mid, confidence: conf, evidence_line: evLine })
      miscHistory.current.push(mid)
      const count = miscHistory.current.filter(x => x === mid).length
      const streak = count >= 2 && miscHistory.current.slice(-2).every(x => x === mid)
      setRecurrenceCount(count)
      setSameStreak(streak)
    } catch (err) {
      const msg = err.response?.data?.detail ?? err.message ?? 'Unknown error.'
      setChatHistory((prev) => [
        ...prev,
        { role: 'bot', content: `⚠️ Error: ${msg}` },
      ])
      setAgentLogs([`> [error] ${msg}`, '> _'])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen w-screen bg-[#1e1e2e] text-[#cdd6f4] overflow-hidden">
      {/* Problem selector sidebar */}
      <ProblemSidebar
        problems={PROBLEMS}
        selected={selectedProblem}
        onSelect={handleSelectProblem}
        isCollapsed={isProblemsCollapsed}
        onToggle={() => setIsProblemsCollapsed((prev) => !prev)}
      />

      {/* Left — Problem description + Code Editor */}
      <CodeEditorPanel
        problem={selectedProblem}
        code={code}
        language={language}
        setCode={setCode}
        isLoading={isLoading}
        onSubmit={handleSubmitCode}
        testResults={testResults}
      />

      {/* Right — Tutor + Terminal */}
      <div className="flex min-w-[280px] w-[32%] max-w-[44rem] flex-col h-full">
        {isTutorCollapsed ? (
          <TutorPanel
            chatHistory={chatHistory}
            chatInput={chatInput}
            setChatInput={setChatInput}
            onSendChat={handleSendChat}
            isChatLoading={isChatLoading}
            isCollapsed={true}
            onToggle={() => setIsTutorCollapsed((prev) => !prev)}
          />
        ) : (
          <IntelligencePanel
            chatHistory={chatHistory}
            chatInput={chatInput}
            setChatInput={setChatInput}
            onSendChat={handleSendChat}
            isChatLoading={isChatLoading}
            terminalCollapsed={isTerminalCollapsed}
            agentLogs={agentLogs}
            misconception={misconception}
            recurrenceCount={recurrenceCount}
            sameStreak={sameStreak}
            testResults={testResults}
          />
        )}
        <AgentTerminal
          agentLogs={agentLogs}
          misconception={misconception}
          recurrenceCount={recurrenceCount}
          isCollapsed={isTerminalCollapsed}
          onToggle={() => setIsTerminalCollapsed((prev) => !prev)}
        />
      </div>
    </div>
  )
}

export default App
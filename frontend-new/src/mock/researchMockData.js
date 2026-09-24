export const researchMockData = {
  execution: {
    passed: '3 / 4 tests passed',
    runtime: '18 ms',
    memory: '14.2 MB',
    status: 'Runtime Error',
    failedTest: {
      input: '] ',
      expected: 'False',
      actual: 'Runtime Error',
      error: 'IndexError: pop from empty list',
      line: 8,
    },
    tests: [
      ['Test 1', '()', 'True', 'True', 'PASSED'],
      ['Test 2', '()[]{}', 'True', 'True', 'PASSED'],
      ['Test 3', '(]', 'False', 'False', 'PASSED'],
      ['Test 4', ']', 'False', 'Runtime Error', 'FAILED'],
    ],
  },
  agents: {
    critic: {
      finding: 'Stack is accessed without checking whether it is empty.',
      evidence: 'stack.pop() on line 8',
    },
    defender: {
      finding: 'Student selected the appropriate stack-based approach.',
      evidence: 'Opening brackets are pushed and compared.',
    },
    judge: {
      finding: 'Correct overall approach, but the empty-stack boundary condition is not handled.',
      evidence: 'Guide the student toward reasoning about stack state.',
    },
  },
  misconception: {
    id: 'M_EMPTY_STACK',
    label: 'Unchecked Empty Stack Access',
    evidence: 'stack.pop() called while stack is empty',
    line: 8,
    confidence: '91%',
  },
  trajectory: [
    ['Attempt 1', 'Detected', 'Conceptual question'],
    ['Attempt 2', 'Repeated', 'Targeted trace question'],
    ['Attempt 3', 'Current', 'Specific edge-case reasoning'],
  ],
  feedback: {
    level: 'Level 2',
    strategy: 'Targeted Socratic Question',
    hint: "Trace the input ']'. What is the state of the stack immediately before pop() is called?",
  },
}

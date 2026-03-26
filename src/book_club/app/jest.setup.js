import '@testing-library/jest-dom'

// Mock fetch globally for tests
global.fetch = jest.fn()

// Reset mocks between tests
beforeEach(() => {
  jest.clearAllMocks()
})

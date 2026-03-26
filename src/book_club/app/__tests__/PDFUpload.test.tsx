import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PDFUpload from '../components/PDFUpload'

// Type the global fetch mock
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

describe('PDFUpload', () => {
  const createMockFile = (name: string, type: string, size: number = 1024): File => {
    const content = new Array(size).fill('x').join('')
    return new File([content], name, { type })
  }

  beforeEach(() => {
    mockFetch.mockReset()
  })

  describe('Rendering', () => {
    it('renders upload area with instructions', () => {
      render(<PDFUpload />)

      expect(screen.getByText(/Click to upload/i)).toBeInTheDocument()
      expect(screen.getByText(/drag and drop/i)).toBeInTheDocument()
      expect(screen.getByText(/PDF files only/i)).toBeInTheDocument()
    })

    it('renders with accessible button role', () => {
      render(<PDFUpload />)

      expect(screen.getByRole('button', { name: /upload pdf file/i })).toBeInTheDocument()
    })
  })

  describe('File Selection', () => {
    it('accepts PDF files via file input', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          filename: 'abc123_test.pdf',
          original_filename: 'test.pdf',
          size_bytes: 1024,
          message: 'PDF uploaded successfully.',
        }),
      } as Response)

      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('test.pdf', 'application/pdf')

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/PDF uploaded successfully/i)).toBeInTheDocument()
      })
    })

    it('rejects non-PDF files client-side', async () => {
      const user = userEvent.setup()
      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('document.txt', 'text/plain')

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/Please select a PDF file/i)).toBeInTheDocument()
      })

      // Should not have called fetch
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('rejects files exceeding size limit', async () => {
      const user = userEvent.setup()
      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      // Create a file larger than 50MB
      const file = createMockFile('large.pdf', 'application/pdf', 51 * 1024 * 1024)

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/exceeds 50MB limit/i)).toBeInTheDocument()
      })

      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('Upload States', () => {
    it('shows uploading state during upload', async () => {
      const user = userEvent.setup()
      // Create a promise we can control
      let resolvePromise: (value: Response) => void
      const pendingPromise = new Promise<Response>((resolve) => {
        resolvePromise = resolve
      })
      mockFetch.mockReturnValueOnce(pendingPromise)

      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('test.pdf', 'application/pdf')

      await user.upload(input, file)

      expect(screen.getByText(/Uploading test.pdf/i)).toBeInTheDocument()

      // Resolve the upload
      resolvePromise!({
        ok: true,
        json: async () => ({ message: 'PDF uploaded successfully.' }),
      } as Response)

      await waitFor(() => {
        expect(screen.getByText(/PDF uploaded successfully/i)).toBeInTheDocument()
      })
    })

    it('shows error state on upload failure', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Server error occurred' }),
      } as Response)

      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('test.pdf', 'application/pdf')

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/Server error occurred/i)).toBeInTheDocument()
      })
    })

    it('shows error on network failure', async () => {
      const user = userEvent.setup()
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('test.pdf', 'application/pdf')

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument()
      })
    })

    it('displays saved filename on success', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          filename: 'abc12345_mybook.pdf',
          message: 'PDF uploaded successfully.',
        }),
      } as Response)

      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('mybook.pdf', 'application/pdf')

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/abc12345_mybook.pdf/i)).toBeInTheDocument()
      })
    })
  })

  describe('Reset Functionality', () => {
    it('shows reset button after successful upload', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'PDF uploaded successfully.' }),
      } as Response)

      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('test.pdf', 'application/pdf')

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/Upload another PDF/i)).toBeInTheDocument()
      })
    })

    it('resets to idle state when clicking reset button', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'PDF uploaded successfully.' }),
      } as Response)

      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('test.pdf', 'application/pdf')

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/PDF uploaded successfully/i)).toBeInTheDocument()
      })

      const resetButton = screen.getByText(/Upload another PDF/i)
      await user.click(resetButton)

      expect(screen.getByText(/Click to upload/i)).toBeInTheDocument()
    })
  })

  describe('API Integration', () => {
    it('sends file to correct endpoint', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'PDF uploaded successfully.' }),
      } as Response)

      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('test.pdf', 'application/pdf')

      await user.upload(input, file)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8010/upload-pdf',
          expect.objectContaining({
            method: 'POST',
            body: expect.any(FormData),
          })
        )
      })
    })

    it('uses NEXT_PUBLIC_API_BASE_URL when set', async () => {
      // Set env var
      const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL
      process.env.NEXT_PUBLIC_API_BASE_URL = 'http://custom-api:9000'

      const user = userEvent.setup()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'PDF uploaded successfully.' }),
      } as Response)

      render(<PDFUpload />)

      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = createMockFile('test.pdf', 'application/pdf')

      await user.upload(input, file)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://custom-api:9000/upload-pdf',
          expect.any(Object)
        )
      })

      // Restore env
      process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv
    })
  })
})

/**
 * Frontend logging utility with console and remote logging
 */

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
}

interface LogEntry {
  level: LogLevel
  message: string
  timestamp: string
  context?: Record<string, any>
  error?: {
    name: string
    message: string
    stack?: string
  }
  userAgent: string
  url: string
  requestId?: string
}

class Logger {
  private apiBase: string
  private requestId: string | null = null
  private context: Record<string, any> = {}

  constructor() {
    this.apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080'
  }

  setRequestId(requestId: string) {
    this.requestId = requestId
  }

  setContext(context: Record<string, any>) {
    this.context = { ...this.context, ...context }
  }

  clearContext() {
    this.context = {}
  }

  private createLogEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, any>,
    error?: Error
  ): LogEntry {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      context: { ...this.context, ...context },
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown',
    }

    if (this.requestId) {
      entry.requestId = this.requestId
    }

    if (error) {
      entry.error = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      }
    }

    return entry
  }

  private logToConsole(entry: LogEntry) {
    const { level, message, context, error } = entry

    const style = this.getConsoleStyle(level)
    const timestamp = new Date().toLocaleTimeString()

    console.log(
      `%c[${timestamp}] [${level.toUpperCase()}]`,
      style,
      message,
      context || {},
      error || ''
    )
  }

  private getConsoleStyle(level: LogLevel): string {
    switch (level) {
      case LogLevel.DEBUG:
        return 'color: #888; font-weight: normal'
      case LogLevel.INFO:
        return 'color: #0066cc; font-weight: bold'
      case LogLevel.WARN:
        return 'color: #ff9800; font-weight: bold'
      case LogLevel.ERROR:
        return 'color: #f44336; font-weight: bold'
      default:
        return ''
    }
  }

  private async sendToRemote(entry: LogEntry) {
    // Only send WARN and ERROR to remote in production
    if (
      process.env.NODE_ENV === 'production' &&
      (entry.level === LogLevel.WARN || entry.level === LogLevel.ERROR)
    ) {
      try {
        // Could send to a logging endpoint
        // For now, we'll skip actual implementation
        // await fetch(`${this.apiBase}/api/v1/logs`, {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(entry),
        // })
      } catch (error) {
        // Silently fail - don't want logging errors to break the app
        console.error('Failed to send log to remote:', error)
      }
    }
  }

  debug(message: string, context?: Record<string, any>) {
    const entry = this.createLogEntry(LogLevel.DEBUG, message, context)
    this.logToConsole(entry)
  }

  info(message: string, context?: Record<string, any>) {
    const entry = this.createLogEntry(LogLevel.INFO, message, context)
    this.logToConsole(entry)
    this.sendToRemote(entry)
  }

  warn(message: string, context?: Record<string, any>) {
    const entry = this.createLogEntry(LogLevel.WARN, message, context)
    this.logToConsole(entry)
    this.sendToRemote(entry)
  }

  error(message: string, error?: Error, context?: Record<string, any>) {
    const entry = this.createLogEntry(LogLevel.ERROR, message, context, error)
    this.logToConsole(entry)
    this.sendToRemote(entry)
  }

  // API call logging
  logApiCall(
    method: string,
    url: string,
    statusCode?: number,
    duration?: number,
    error?: Error
  ) {
    const context = {
      method,
      url,
      statusCode,
      duration,
    }

    if (error) {
      this.error(`API call failed: ${method} ${url}`, error, context)
    } else {
      this.debug(`API call: ${method} ${url}`, context)
    }
  }

  // Component lifecycle logging
  logComponentMount(componentName: string, props?: Record<string, any>) {
    this.debug(`Component mounted: ${componentName}`, { componentName, props })
  }

  logComponentUnmount(componentName: string) {
    this.debug(`Component unmounted: ${componentName}`, { componentName })
  }

  // User action logging
  logUserAction(action: string, details?: Record<string, any>) {
    this.info(`User action: ${action}`, { action, ...details })
  }

  // Performance logging
  logPerformance(metric: string, value: number, unit: string = 'ms') {
    this.info(`Performance: ${metric}`, { metric, value, unit })
  }
}

// Create singleton instance
const logger = new Logger()

// Add global error handler
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    logger.error('Uncaught error', event.error, {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    })
  })

  window.addEventListener('unhandledrejection', (event) => {
    logger.error('Unhandled promise rejection', event.reason, {
      reason: event.reason,
    })
  })
}

export default logger

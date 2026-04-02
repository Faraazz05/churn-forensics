import { triggerPdfReport, triggerExcelReport } from '../api/reports'

export const useExport = () => {
  return {
    exportPdf: triggerPdfReport,
    exportExcel: triggerExcelReport,
  }
}

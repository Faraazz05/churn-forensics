import { apiClient } from './client';

export const triggerPdfReport = async () => {
  const response = await apiClient.get<Blob>('/report/pdf', { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response as any]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `Customer_Health_Report_${new Date().toISOString().split('T')[0]}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

export const triggerExcelReport = async () => {
  const response = await apiClient.get<Blob>('/report/excel', { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response as any]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `Customer_Health_Data_${new Date().toISOString().split('T')[0]}.xlsx`);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

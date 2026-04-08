/**
 * Admin service — wraps /api/v1/admin/* endpoints.
 * Derived from COADM01C (CICS transaction CA00).
 */
import client from './apiClient';
import type { AdminMenuResponse, AdminMenuItem } from '@/lib/types/api';

export const adminService = {
  /**
   * GET /api/v1/admin/menu
   * Derived from COADM01C BUILD-MENU-OPTIONS paragraph.
   */
  async getAdminMenu(): Promise<AdminMenuResponse> {
    const { data } = await client.get<AdminMenuResponse>('/admin/menu');
    return data;
  },

  /**
   * GET /api/v1/admin/menu/{option}
   * Derived from COADM01C PROCESS-ENTER-KEY paragraph.
   */
  async getAdminMenuOption(option: number): Promise<AdminMenuItem> {
    const { data } = await client.get<AdminMenuItem>(`/admin/menu/${option}`);
    return data;
  },
};

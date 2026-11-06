// Auth and account-management calls. The session lives in an HttpOnly cookie,
// so no token handling is needed in the browser.

import { request } from './api';

export type Role = 'owner' | 'admin' | 'staff';

export type CurrentUser = {
  username: string;
  role: Role;
  must_change_password: boolean;
};

export type StaffUser = {
  id: number;
  username: string;
  role: Role;
  is_active: boolean;
  must_change_password: boolean;
  created_by: string | null;
};

export function login(
  username: string,
  password: string,
): Promise<CurrentUser> {
  return request<CurrentUser>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export function logout(): Promise<{ status: string }> {
  return request<{ status: string }>('/auth/logout', { method: 'POST' });
}

export function me(): Promise<CurrentUser> {
  return request<CurrentUser>('/auth/me');
}

export function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<{ status: string }> {
  return request<{ status: string }>('/auth/password', {
    method: 'POST',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}

export function listUsers(): Promise<StaffUser[]> {
  return request<StaffUser[]>('/users');
}

export function createUser(payload: {
  username: string;
  password: string;
  role: Role;
}): Promise<StaffUser> {
  return request<StaffUser>('/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateUser(
  id: number,
  payload: { role?: Role; is_active?: boolean },
): Promise<StaffUser> {
  return request<StaffUser>(`/users/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function resetUserPassword(
  id: number,
  newPassword: string,
): Promise<{ id: number; status: string }> {
  return request<{ id: number; status: string }>(
    `/users/${id}/reset-password`,
    {
      method: 'POST',
      body: JSON.stringify({ new_password: newPassword }),
    },
  );
}

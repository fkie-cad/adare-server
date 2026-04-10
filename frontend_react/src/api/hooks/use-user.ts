import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { endpoints } from '@/api/endpoints'
import type { Profile } from '@/types/experiment'
import { useAuthStore } from '@/stores/auth-store'

export function useLoggedInUser() {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn)

  return useQuery({
    queryKey: ['logged-in-user'],
    queryFn: async () => {
      const { data } = await api.get<Profile>(endpoints.userProfile)
      return data
    },
    enabled: isLoggedIn,
  })
}

export function useIsSupervisor(): boolean {
  const { data: profile } = useLoggedInUser()
  if (!profile) return false
  return profile.teams.some((t) => t.name === 'supervisor' || t.name === 'admin')
}

export function useUserProfile(username: string) {
  return useQuery({
    queryKey: ['user-profile', username],
    queryFn: async () => {
      const { data } = await api.get<Profile>(endpoints.userProfileByName(username))
      return data
    },
    enabled: !!username,
  })
}

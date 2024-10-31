interface Achievement {
  name: string;
  iconfile: string;
  description: string;
  count: number;
}

export interface Team {
  id: number;
  name: string;
}

interface UserInfo {
  [username: string]: {
    avatar: string;
    email: string;
    teams: Team[];
    achievements: Achievement[];
  };
}

export type { Achievement, UserInfo };

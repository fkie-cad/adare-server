interface Achievement {
  name: string;
  iconfile: string;
  description: string;
  count: number;
}

interface UserInfo {
  [username: string]: {
    avatar: string;
    email: string;
    teams: [];
    achievements: Achievement[];
  };
}

export type { Achievement, UserInfo };

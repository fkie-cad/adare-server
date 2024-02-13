interface Achievement {
  name: string;
  iconfile: string;
  description: string;
  count: number;
}

interface UserInfo {
  [username: string]: {
    avatar: any;
    email: string;
    groups: [];
    achievements: Achievement[];
  };
}

export type { Achievement, UserInfo };

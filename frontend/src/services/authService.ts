
// This is a mock implementation. In a real app, you would use AWS Cognito SDK.
// For now, we'll simulate the API calls for development purposes.

interface User {
  id: string;
  username: string;
  email: string;
  avatarUrl?: string;
}

// Mock user data for development
const MOCK_USERS = [
  {
    id: "1",
    username: "johndoe",
    email: "john@example.com",
    password: "password123",
    avatarUrl: "https://i.pravatar.cc/150?u=johndoe",
  },
];

// Simulate latency for a more realistic experience
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Store user in localStorage for persistence
const saveUserToStorage = (user: User) => {
  localStorage.setItem("user", JSON.stringify(user));
};

const removeUserFromStorage = () => {
  localStorage.removeItem("user");
};

// Mock login function
export const login = async (email: string, password: string): Promise<User> => {
  await delay(800); // Simulate network request

  const user = MOCK_USERS.find(
    (u) => u.email === email && u.password === password
  );

  if (!user) {
    throw new Error("Invalid email or password");
  }

  const { password: _, ...userWithoutPassword } = user;
  saveUserToStorage(userWithoutPassword);
  
  return userWithoutPassword;
};

// Mock register function
export const register = async (
  username: string,
  email: string,
  password: string
): Promise<User> => {
  await delay(800); // Simulate network request

  // Check if user already exists
  if (MOCK_USERS.some((u) => u.email === email)) {
    throw new Error("User with this email already exists");
  }

  const newUser = {
    id: Date.now().toString(),
    username,
    email,
    password,
    avatarUrl: `https://i.pravatar.cc/150?u=${username}`,
  };

  // In a real app, this would be saved to a database
  MOCK_USERS.push(newUser);

  const { password: _, ...userWithoutPassword } = newUser;
  saveUserToStorage(userWithoutPassword);
  
  return userWithoutPassword;
};

// Mock logout function
export const logout = async (): Promise<void> => {
  await delay(300); // Simulate network request
  removeUserFromStorage();
};

// Mock getCurrentUser function
export const getCurrentUser = async (): Promise<User | null> => {
  await delay(300); // Simulate network request
  
  const storedUser = localStorage.getItem("user");
  
  if (!storedUser) {
    return null;
  }
  
  return JSON.parse(storedUser);
};

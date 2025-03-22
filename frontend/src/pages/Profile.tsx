
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LogOut, Key, Save } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";

const Profile: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [prefQuality, setPrefQuality] = useState<string>(localStorage.getItem("preferredQuality") || "auto");
  const [prefVolume, setPrefVolume] = useState<number>(
    parseInt(localStorage.getItem("preferredVolume") || "70")
  );
  const [prefBrightness, setPrefBrightness] = useState<number>(
    parseInt(localStorage.getItem("preferredBrightness") || "100")
  );
  const [oldPassword, setOldPassword] = useState<string>("");
  const [newPassword, setNewPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");
  const [isDialogOpen, setIsDialogOpen] = useState<boolean>(false);

  if (!user) {
    navigate("/login");
    return null;
  }

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const handleChangePassword = () => {
    if (newPassword !== confirmPassword) {
      toast.error("New passwords don't match");
      return;
    }

    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    toast.success("Password changed successfully");
    setIsDialogOpen(false);
    setOldPassword("");
    setNewPassword("");
    setConfirmPassword("");
  };

  const saveStreamPreferences = () => {
    localStorage.setItem("preferredQuality", prefQuality);
    localStorage.setItem("preferredVolume", prefVolume.toString());
    localStorage.setItem("preferredBrightness", prefBrightness.toString());
    toast.success("Stream preferences saved");
  };

  return (
    <div className="container mx-auto py-24 px-4 md:px-6">
      <div className="grid gap-6 md:grid-cols-2">
        {/* User Info */}
        <Card className="md:col-span-2">
          <CardHeader className="flex flex-col items-center space-y-4">
            <Avatar className="h-24 w-24">
              <AvatarImage src={user.avatarUrl} alt={user.username} />
              <AvatarFallback className="text-2xl">{user.username.substring(0, 2).toUpperCase()}</AvatarFallback>
            </Avatar>
            <div className="space-y-1 text-center">
              <CardTitle className="text-2xl">{user.username}</CardTitle>
              <CardDescription>{user.email}</CardDescription>
            </div>
          </CardHeader>
        </Card>

        {/* Basic Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Account Settings</CardTitle>
            <CardDescription>Manage your account settings and security</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col space-y-2">
              <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="w-full justify-start">
                    <Key className="mr-2 h-4 w-4" />
                    Change Password
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Change Password</DialogTitle>
                    <DialogDescription>
                      Enter your current password and your new password below.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <label htmlFor="old-password">Current Password</label>
                      <Input
                        id="old-password"
                        type="password"
                        value={oldPassword}
                        onChange={(e) => setOldPassword(e.target.value)}
                      />
                    </div>
                    <div className="grid gap-2">
                      <label htmlFor="new-password">New Password</label>
                      <Input
                        id="new-password"
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                      />
                    </div>
                    <div className="grid gap-2">
                      <label htmlFor="confirm-password">Confirm New Password</label>
                      <Input
                        id="confirm-password"
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleChangePassword}>Save Changes</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
            <Button
              variant="destructive"
              className="w-full justify-start"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </CardContent>
        </Card>

        {/* Stream Preferences */}
        <Card>
          <CardHeader>
            <CardTitle>Stream Preferences</CardTitle>
            <CardDescription>Customize your viewing experience</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="quality" className="font-medium">
                Preferred Stream Quality
              </label>
              <select
                id="quality"
                className="w-full rounded-md border border-input bg-background px-3 py-2"
                value={prefQuality}
                onChange={(e) => setPrefQuality(e.target.value)}
              >
                <option value="auto">Auto</option>
                <option value="720p">720p</option>
                <option value="1080p">1080p</option>
              </select>
            </div>
            <div className="space-y-2">
              <label htmlFor="volume" className="font-medium">
                Default Volume: {prefVolume}%
              </label>
              <Slider
                id="volume"
                min={0}
                max={100}
                step={1}
                value={[prefVolume]}
                onValueChange={(value) => setPrefVolume(value[0])}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="brightness" className="font-medium">
                Default Brightness: {prefBrightness}%
              </label>
              <Slider
                id="brightness"
                min={10}
                max={200}
                step={1}
                value={[prefBrightness]}
                onValueChange={(value) => setPrefBrightness(value[0])}
              />
            </div>
          </CardContent>
          <CardFooter>
            <Button className="ml-auto" onClick={saveStreamPreferences}>
              <Save className="mr-2 h-4 w-4" />
              Save Preferences
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default Profile;

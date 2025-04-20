// import React, { useState } from "react";
// import { useNavigate } from "react-router-dom";
// import Navbar from "@/components/Navbar";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
// import { Input } from "@/components/ui/input";
// import { Button } from "@/components/ui/button";
// import { Label } from "@/components/ui/label";
// import { toast } from "sonner";

// const Login: React.FC = () => {
//   const navigate = useNavigate();
//   const [userId, setUserId] = useState<string>("");

//   const handleSubmit = (e: React.FormEvent) => {
//     e.preventDefault();
//     if (!userId.trim()) {
//       toast.error("Please enter a valid User ID");
//       return;
//     }
//     navigate(`/dashboard/${userId}`);
//   };

//   return (
//     <div className="min-h-screen bg-background page-transition">
//       <Navbar />
//       <div className="container flex items-center justify-center min-h-screen pt-16 pb-8 px-4">
//         <div className="w-full max-w-md">
//           <Card className="border-border shadow-sm">
//             <CardHeader className="space-y-1">
//               <CardTitle className="text-2xl font-bold text-center">Connect to Stream</CardTitle>
//               <CardDescription className="text-center">
//                 Enter your User ID to start streaming
//               </CardDescription>
//             </CardHeader>
//             <CardContent>
//               <form onSubmit={handleSubmit} className="space-y-4">
//                 <div className="space-y-2">
//                   <Label htmlFor="userId">User ID</Label>
//                   <Input
//                     id="userId"
//                     type="text"
//                     placeholder="Enter your User ID"
//                     value={userId}
//                     onChange={(e) => setUserId(e.target.value)}
//                     required
//                   />
//                 </div>
//                 <Button type="submit" className="w-full">
//                   Connect
//                 </Button>
//               </form>
//             </CardContent>
//           </Card>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default Login;




import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [userId, setUserId] = useState<string>("");
  const [userList, setUserList] = useState<string[]>([]);

  useEffect(() => {
    fetch("http://localhost:5001/users")
      .then((res) => res.json())
      .then((data) => setUserList(data))
      .catch((err) => {
        console.error("Error fetching users:", err);
        toast.error("Failed to load users");
      });
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId.trim()) {
      toast.error("Please select a User ID");
      return;
    }
    navigate(`/dashboard/${userId}`);
  };

  return (
    <div className="min-h-screen bg-background page-transition">
      <Navbar />
      <div className="container flex items-center justify-center min-h-screen pt-16 pb-8 px-4">
        <div className="w-full max-w-md">
          <Card className="border-border shadow-sm">
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl font-bold text-center">Connect to Stream</CardTitle>
              <CardDescription className="text-center">
                Select a channel to start streaming
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="userId">Channels</Label>
                  <select
                    id="userId"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 bg-background"
                    required
                  >
                    <option value="" disabled>Select a Channel</option>
                    {userList.map((user) => (
                      <option key={user} value={user}>
                        {user}
                      </option>
                    ))}
                  </select>
                </div>
                <Button type="submit" className="w-full">
                  Connect
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Login;
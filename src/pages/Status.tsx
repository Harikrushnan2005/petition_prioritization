import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSub, DropdownMenuSubTrigger, DropdownMenuSubContent } from "@/components/ui/dropdown-menu";
import { FileText, Download, Upload, RefreshCcw, ArrowLeft, Menu } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useNavigate, useParams } from "react-router-dom";

interface Petition {
  id: number;
  file_name: string;
  file_path: string;
  department: string;
  priority: string;
  email_sent: boolean;
  status: string;
  ack_token: string;
  work_completed_date: string | null;
  work_completed_file: string | null;
  created_at: string;
}

export default function Status() {
  const [petitions, setPetitions] = useState<Petition[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();
  const navigate = useNavigate();
  const { department } = useParams();
  const userRole = localStorage.getItem('userRole');
  const userDepartment = localStorage.getItem('userDepartment');

  const filteredPetitions = department 
    ? petitions.filter(p => p.department.toLowerCase() === department.toLowerCase())
    : petitions;

  const fetchPetitions = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/petitions");
      const data = await response.json();
      setPetitions(data.petitions);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch petitions",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPetitions();
  }, []);

  const handleFileUpload = async (id: number, file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`http://127.0.0.1:5000/api/petitions/${id}/complete`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        toast({
          title: "Success",
          description: "Work completion document uploaded",
        });
        fetchPetitions();
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to upload document",
        variant: "destructive",
      });
    }
  };

  const getStatusBadge = (status: string, emailSent: boolean) => {
    const colors = {
      "Not Sent": "bg-gray-500",
      Sent: "bg-blue-500",
      Acknowledged: "bg-yellow-500",
      "In Progress": "bg-orange-500",
      Completed: "bg-green-500",
    };
    const displayStatus = !emailSent ? "Not Sent" : status;
    return (
      <Badge className={colors[displayStatus as keyof typeof colors] || "bg-gray-500"}>
        {displayStatus}
      </Badge>
    );
  };

  const getPriorityBadge = (priority: string) => {
    const colors = {
      urgent: "bg-red-500",
      neutral: "bg-yellow-500",
      later: "bg-green-500",
    };
    return (
      <Badge className={colors[priority as keyof typeof colors] || "bg-gray-500"}>
        {priority}
      </Badge>
    );
  };

  if (loading) {
    return <div className="container mx-auto p-6">Loading...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-4">
        <Button
          variant="outline"
          onClick={() => navigate("/")}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon">
              <Menu className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                Status
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                {userRole === 'admin' ? (
                  <>
                    <DropdownMenuItem onClick={() => navigate("/status")}>
                      All Departments
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/status/water")}>
                      Water Department
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/status/electricity")}>
                      Electricity Department
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/status/civil")}>
                      Civil Department
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/status/crime")}>
                      Crime Department
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/status/sanitation")}>
                      Sanitation Department
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/status/roads")}>
                      Roads Department
                    </DropdownMenuItem>
                  </>
                ) : (
                  <DropdownMenuItem onClick={() => navigate(`/status/${userDepartment?.toLowerCase()}`)}>
                    {userDepartment} Department
                  </DropdownMenuItem>
                )}
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            <DropdownMenuItem onClick={() => {
              localStorage.removeItem("isLoggedIn");
              localStorage.removeItem("username");
              localStorage.removeItem("userRole");
              localStorage.removeItem("userDepartment");
              navigate("/login");
            }}>
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-2xl font-bold">
            {department ? `${department.charAt(0).toUpperCase() + department.slice(1)} Department` : 'All Departments'} - Petition Status
          </CardTitle>
          <Button onClick={fetchPetitions} size="sm">
            <RefreshCcw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>File Name</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Email Sent</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Ack Token</TableHead>
                  <TableHead>Created At</TableHead>
                  <TableHead>Completed Date</TableHead>
                  <TableHead>Petition PDF</TableHead>
                  <TableHead>Work PDF</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPetitions.map((petition) => (
                  <TableRow key={petition.id}>
                    <TableCell>{petition.id}</TableCell>
                    <TableCell>{petition.file_name}</TableCell>
                    <TableCell className="capitalize">{petition.department}</TableCell>
                    <TableCell>{getPriorityBadge(petition.priority)}</TableCell>
                    <TableCell>{petition.email_sent ? "✓" : "✗"}</TableCell>
                    <TableCell>{getStatusBadge(petition.status, petition.email_sent)}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {petition.ack_token?.substring(0, 8)}...
                    </TableCell>
                    <TableCell>{new Date(petition.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      {petition.work_completed_date
                        ? new Date(petition.work_completed_date).toLocaleDateString()
                        : "-"}
                    </TableCell>
                    <TableCell>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => window.open(`http://127.0.0.1:5000/api/petitions/${petition.id}/file`, '_blank')}
                      >
                        <FileText className="h-4 w-4 mr-1" />
                        View
                      </Button>
                    </TableCell>
                    <TableCell>
                      {petition.work_completed_file ? (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => window.open(`http://127.0.0.1:5000/api/petitions/${petition.id}/work-file`, '_blank')}
                        >
                          <Download className="h-4 w-4 mr-1" />
                          Download
                        </Button>
                      ) : (
                        <label>
                          <input
                            type="file"
                            className="hidden"
                            accept=".pdf,.jpg,.png"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) handleFileUpload(petition.id, file);
                            }}
                          />
                          <Button size="sm" variant="outline" asChild>
                            <span>
                              <Upload className="h-4 w-4 mr-1" />
                              Upload
                            </span>
                          </Button>
                        </label>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-normal">
                        {!petition.email_sent ? "Not Sent" : petition.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import { useState, useEffect } from "react";
import { FileUpload } from "@/components/FileUpload";
import { ClassificationResults } from "@/components/ClassificationResults";
import { StatisticsDashboard } from "@/components/StatisticsDashboard";
import { FileText, Sparkles, Menu, BarChart3, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSub, DropdownMenuSubTrigger, DropdownMenuSubContent } from "@/components/ui/dropdown-menu";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";

export interface ClassifiedComplaint {
  id: string;
  text: string;
  priority: "urgent" | "neutral" | "later";
  timestamp: Date;
  fileName: string;
  department: string;
  email_sent: boolean;
}

const Index = () => {
  const [complaints, setComplaints] = useState<ClassifiedComplaint[]>([]);
  const [petitions, setPetitions] = useState<any[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
    const userRole = sessionStorage.getItem('userRole');
  const userDepartment = sessionStorage.getItem('userDepartment');


  useEffect(() => {
    fetchPetitions();
  }, []);

  const fetchPetitions = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/petitions');
      const data = await response.json();

      if (data.petitions) {
        setPetitions(data.petitions);
        const mapped = data.petitions.map((p: any) => ({
          id: p.id.toString(),
          text: p.extracted_text,
          priority: p.priority as "urgent" | "neutral" | "later",
          timestamp: new Date(p.created_at),
          fileName: p.file_name,
          department: p.department,
          email_sent: p.email_sent || false,
        }));
        setComplaints(mapped);
      }
    } catch (error) {
      console.error("Error fetching petitions:", error);
    }
  };

  const handleFileUpload = async (files: File[]) => {
    setIsProcessing(true);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      toast({
        title: "Classification complete",
        description: `Successfully classified ${files.length} petition${files.length > 1 ? 's' : ''}`,
      });

      await fetchPetitions();
    } catch (error) {
      console.error("Error processing files:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to process petitions",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-primary rounded-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-foreground">PrioritySort</h1>
                <p className="text-sm text-muted-foreground">Priority detection in scanned complaints using OCR and ML</p>
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon">
                  <Menu className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <BarChart3 className="h-4 w-4 mr-2" />
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
                <DropdownMenuItem 
                  onClick={() => {
                    sessionStorage.removeItem("isLoggedIn");
                    sessionStorage.removeItem("username");
                    sessionStorage.removeItem("userRole");
                    sessionStorage.removeItem("userDepartment");
                    navigate("/login");
                  }}
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Statistics Dashboard */}
        {petitions.length > 0 && <StatisticsDashboard petitions={petitions} />}

        {/* Upload Section */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-primary" />
            <h2 className="text-2xl font-semibold text-foreground">Upload Petitions</h2>
          </div>
          <p className="text-muted-foreground mb-6">
            Upload scanned petition documents. Our AI will extract text using OCR and automatically classify them by priority.
          </p>
          <FileUpload onUpload={handleFileUpload} isProcessing={isProcessing} />
        </div>

        {/* Results Section */}
        {complaints.length > 0 && (
          <div>
            <h2 className="text-2xl font-semibold text-foreground mb-6">
              Classified Complaints ({complaints.length})
            </h2>
            <ClassificationResults 
              complaints={complaints} 
              onEmailSent={fetchPetitions} 
              onHistoryCleared={fetchPetitions}
            />
          </div>
        )}

        {/* Empty State */}
        {complaints.length === 0 && !isProcessing && (
          <div className="text-center py-16">
            <div className="inline-flex p-4 bg-muted rounded-full mb-4">
              <FileText className="w-12 h-12 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-medium text-foreground mb-2">No complaints yet</h3>
            <p className="text-muted-foreground">Upload your first petition document to get started</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default Index;

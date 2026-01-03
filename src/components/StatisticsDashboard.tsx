import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, AlertCircle, Clock, CheckCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface Petition {
  id: string;
  department: string;
  priority: string;
  email_sent: boolean | null;
  created_at: string;
}

interface StatisticsDashboardProps {
  petitions: Petition[];
}

export const StatisticsDashboard = ({ petitions }: StatisticsDashboardProps) => {
  const totalPetitions = petitions.length;
  const urgentCount = petitions.filter(p => p.priority === "urgent").length;
  const neutralCount = petitions.filter(p => p.priority === "neutral").length;
  const laterCount = petitions.filter(p => p.priority === "later").length;
  const emailsSent = petitions.filter(p => p.email_sent).length;


  return (
    <div className="space-y-6 mb-8">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Petitions</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPetitions}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Urgent</CardTitle>
            <AlertCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{urgentCount}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Neutral</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{neutralCount}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Later</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{laterCount}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Email Notifications Sent</CardTitle>
          <CheckCircle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{emailsSent}</div>
          <p className="text-xs text-muted-foreground mt-1">
            {totalPetitions > 0 ? `${Math.round((emailsSent / totalPetitions) * 100)}%` : '0%'} of total
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

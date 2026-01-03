import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface DepartmentSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

const departments = [
  "Water",
  "Electricity",
  "Civil",
  "Crime",
  "Sanitation",
  "Roads",
];

export const DepartmentSelector = ({ value, onChange }: DepartmentSelectorProps) => {
  return (
    <div className="space-y-2">
      <Label htmlFor="department">Target Department</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id="department">
          <SelectValue placeholder="Select department" />
        </SelectTrigger>
        <SelectContent>
          {departments.map((dept) => (
            <SelectItem key={dept} value={dept}>
              {dept}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

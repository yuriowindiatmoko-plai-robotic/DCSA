<script setup lang="ts">
import { ref, watch } from "vue";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Save, Plus, Trash2 } from "lucide-vue-next";
import { Badge } from "@/components/ui/badge";
import axios from "axios";
import { useAuthStore } from "@/stores/auth";

// Props & Emits
const props = withDefaults(
  defineProps<{
    open: boolean;
    order: any;
  }>(),
  {},
);

const emit = defineEmits(["update:open", "saved"]);

const authStore = useAuthStore();
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Types
interface MenuItem {
  menu: string;
  total_qty: number;
}

interface MenuDetails {
  heavy_meal?: MenuItem[];
  snack?: MenuItem[];
  beverages?: MenuItem[];
}

interface StaffAllocation {
  category: string;
  total: number;
  drop_off_location: string;
  serving_type: string;
}

// Local State
const isSaving = ref(false);

// Staff Allocation State - Editable directly
const staffAllocations = ref<StaffAllocation[]>([]);

// Menu Details State - Editable directly
const menuDetails = ref<MenuDetails>({
  heavy_meal: [],
  snack: [],
  beverages: [],
});

// Menu categories for display
const menuCategories = [
  {
    key: "heavy_meal",
    label: "Heavy Meal",
    color: "bg-orange-50 text-orange-700 border-orange-200",
  },
  {
    key: "snack",
    label: "Snack",
    color: "bg-purple-50 text-purple-700 border-purple-200",
  },
  {
    key: "beverages",
    label: "Beverages",
    color: "bg-blue-50 text-blue-700 border-blue-200",
  },
];

// Add staff allocation item helper
const addStaffAllocation = () => {
  staffAllocations.value.push({
    category: "",
    total: 0,
    drop_off_location: "",
    serving_type: "",
  });
};

// Remove staff allocation item helper
const removeStaffAllocation = (index: number) => {
  staffAllocations.value.splice(index, 1);
};

// Add menu item helper
const addMenuItem = (category: keyof MenuDetails) => {
  if (!menuDetails.value[category]) {
    menuDetails.value[category] = [];
  }
  menuDetails.value[category]!.push({ menu: "", total_qty: 0 });
};

// Remove menu item helper
const removeMenuItem = (category: keyof MenuDetails, index: number) => {
  if (menuDetails.value[category]) {
    menuDetails.value[category]!.splice(index, 1);
  }
};

// Watch for prop changes to update local state
watch(
  () => props.order,
  (newOrder) => {
    if (newOrder) {
      // Load staff allocation
      if (newOrder.staff_allocation) {
        const allocations: StaffAllocation[] = [];
        for (const [key, value] of Object.entries(newOrder.staff_allocation)) {
          if (typeof value === "object" && value !== null) {
            allocations.push({
              category: key,
              total: (value as any).total || 0,
              drop_off_location: (value as any).drop_off_location || "",
              serving_type: (value as any).serving_type || "",
            });
          }
        }
        staffAllocations.value = allocations;
      } else {
        staffAllocations.value = [];
      }

      // Load menu details
      if (newOrder.menu_details) {
        menuDetails.value = JSON.parse(JSON.stringify(newOrder.menu_details));
      } else {
        menuDetails.value = { heavy_meal: [], snack: [], beverages: [] };
      }
    }
  },
  { immediate: true },
);

const handleSave = async () => {
  if (!props.order) return;

  try {
    isSaving.value = true;

    // Convert staffAllocations to staff_allocation format
    const staffAllocation: Record<
      string,
      { total: number; drop_off_location: string; serving_type: string }
    > = {};
    for (const item of staffAllocations.value) {
      if (item.category) {
        staffAllocation[item.category] = {
          total: item.total || 0,
          drop_off_location: item.drop_off_location || "",
          serving_type: item.serving_type || "",
        };
      }
    }

    // Prepare update payload
    const updateData: any = {
      staff_allocation: staffAllocation,
      menu_details: menuDetails.value,
    };

    // Calculate total_portion from staff allocation
    const calculatedTotal = Object.values(staffAllocation).reduce(
      (sum, item) => sum + item.total,
      0,
    );
    updateData.total_portion = calculatedTotal;

    await axios.put(
      `${API_URL}/api/orders/${props.order.order_id}`,
      updateData,
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authStore.token}`,
        },
      },
    );

    emit("saved");
    emit("update:open", false);
  } catch (error: any) {
    console.error("Failed to save order:", error);
    alert(`Failed to save: ${error.response?.data?.detail || error.message}`);
  } finally {
    isSaving.value = false;
  }
};

const handleClose = () => {
  emit("update:open", false);
};
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent
      class="max-w-[800px] p-0 overflow-hidden bg-white"
      style="height: 85vh"
    >
      <!-- Header Area - Fixed -->
      <div
        class="bg-zinc-50 border-b border-zinc-100 p-6 flex items-center justify-between shrink-0"
      >
        <div>
          <div class="flex items-center gap-3 mb-1">
            <h2 class="text-xl font-bold text-zinc-900">
              Edit Order: {{ order?.order_id?.slice(0, 8) || "N/A" }}...
            </h2>
            <Badge
              variant="outline"
              class="bg-blue-50 text-blue-700 border-blue-200"
            >
              {{ order?.status || "DRAFT" }}
            </Badge>
          </div>
          <p class="text-sm text-zinc-500">
            Edit staff allocation and menu details, then submit changes.
          </p>
        </div>

        <div class="text-right">
          <div class="text-sm font-medium text-zinc-900">
            {{ order?.institution_name || "-" }}
          </div>
          <div class="text-xs text-zinc-500">
            {{ order?.order_date || "-" }}
          </div>
        </div>
      </div>

      <!-- Body - Scrollable -->
      <div
        class="p-6 space-y-6 overflow-y-auto"
        style="max-height: calc(85vh - 160px)"
      >
        <!-- Section: Staff Allocation -->
        <div class="space-y-4">
          <div class="flex items-center justify-between border-b pb-2">
            <h3 class="font-bold text-zinc-700 text-sm uppercase tracking-wide">
              Staff Allocation
            </h3>
            <Button
              variant="ghost"
              size="sm"
              @click="addStaffAllocation"
              class="h-7 px-2 text-xs gap-1 text-emerald-600 hover:bg-emerald-50"
            >
              <Plus class="h-3 w-3" />
              Add Staff
            </Button>
          </div>

          <div class="border rounded-lg overflow-hidden bg-white">
            <Table>
              <TableHeader class="bg-zinc-50/50">
                <TableRow>
                  <TableHead>Category/Staff</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead class="text-center w-[100px]">Qty</TableHead>
                  <TableHead class="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="(item, idx) in staffAllocations"
                  :key="idx"
                  class="group"
                >
                  <TableCell>
                    <Input
                      v-model="item.category"
                      placeholder="Staff name"
                      class="h-8 bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      v-model="item.drop_off_location"
                      placeholder="Location"
                      class="h-8 bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      v-model="item.serving_type"
                      placeholder="Type"
                      class="h-8 bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      v-model.number="item.total"
                      type="number"
                      placeholder="0"
                      class="h-8 w-20 text-center bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      @click="removeStaffAllocation(idx)"
                      class="h-8 w-8 text-zinc-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 class="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
                <TableRow v-if="staffAllocations.length === 0">
                  <TableCell
                    colspan="5"
                    class="text-center py-8 text-zinc-400 text-sm"
                  >
                    No staff allocation items. Click "Add Staff" to add items.
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </div>

        <!-- Section: Menu Details -->
        <div class="border-t border-zinc-100 pt-6 space-y-6">
          <div class="flex items-center justify-between">
            <h3 class="font-bold text-zinc-700 text-sm uppercase tracking-wide">
              Menu Details
            </h3>
            <Badge
              variant="outline"
              class="bg-indigo-50 text-indigo-700 border-indigo-200"
            >
              Add-on Items
            </Badge>
          </div>

          <div class="grid grid-cols-1 gap-4">
            <!-- Menu Category Cards -->
            <div
              v-for="category in menuCategories"
              :key="category.key"
              class="border rounded-lg bg-white overflow-hidden"
            >
              <div
                class="px-4 py-2 border-b flex items-center justify-between"
                :class="category.color"
              >
                <span class="font-semibold text-xs uppercase">{{
                  category.label
                }}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  @click="addMenuItem(category.key as keyof MenuDetails)"
                  class="h-6 px-2 text-xs opacity-70 hover:opacity-100"
                >
                  <Plus class="h-3 w-3 mr-1" />
                  Add Item
                </Button>
              </div>

              <div class="divide-y divide-zinc-50">
                <div
                  v-for="(item, idx) in menuDetails[
                    category.key as keyof MenuDetails
                  ]"
                  :key="idx"
                  class="p-3 flex items-center gap-3 group"
                >
                  <div class="flex-1 grid grid-cols-2 gap-3">
                    <div>
                      <label
                        class="text-[10px] font-semibold text-zinc-500 uppercase"
                        >Menu Name</label
                      >
                      <Input
                        v-model="item.menu"
                        placeholder="Enter menu name"
                        class="h-8 text-sm"
                      />
                    </div>
                    <div>
                      <label
                        class="text-[10px] font-semibold text-zinc-500 uppercase"
                        >Quantity</label
                      >
                      <Input
                        v-model.number="item.total_qty"
                        type="number"
                        placeholder="0"
                        class="h-8 text-sm"
                      />
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    @click="
                      removeMenuItem(category.key as keyof MenuDetails, idx)
                    "
                    class="h-8 w-8 text-zinc-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 class="h-4 w-4" />
                  </Button>
                </div>
                <div
                  v-if="!menuDetails[category.key as keyof MenuDetails]?.length"
                  class="p-4 text-center text-zinc-400 text-sm"
                >
                  No items in {{ category.label.toLowerCase() }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer - Fixed -->
      <div class="p-6 bg-zinc-50 border-t border-zinc-100 shrink-0">
        <div class="w-full flex items-center justify-between">
          <Button variant="ghost" @click="handleClose" :disabled="isSaving">
            Cancel
          </Button>

          <Button
            class="bg-emerald-600 hover:bg-emerald-700 text-white gap-2"
            :disabled="isSaving"
            @click="handleSave"
          >
            <Save class="h-4 w-4" />
            {{ isSaving ? "Saving..." : "Submit Changes" }}
          </Button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Trash2, CheckCircle2 } from "lucide-vue-next";
import { Badge } from "@/components/ui/badge";
import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { onMounted, computed } from "vue";

// Props & Emits
const props = withDefaults(
  defineProps<{
    open: boolean;
  }>(),
  {},
);

const emit = defineEmits(["update:open", "order-created"]);

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

interface Institution {
  institution_id: string;
  name: string;
}

// Local State
const isSubmitting = ref(false);
const servingDate = ref("");
const droppingLocationFood = ref("");

// Institution State
const institutions = ref<Institution[]>([]);
const selectedInstitutionId = ref<string>("");

const canSelectInstitution = computed(() => {
  const role = authStore.userRole;
  return role === "DK_ADMIN" || role === "SUPER_ADMIN";
});

// Simplified Staff Allocation State
// Requirement: Hardcoded key "all_guest"
const staffAllocation = ref({
  total: 20,
  serving_type: "prasmanan",
  drop_off_location: "Pantry",
});

// Menu Details State
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

const resetForm = () => {
  servingDate.value = "";
  droppingLocationFood.value = "";
  staffAllocation.value = {
    total: 20,
    serving_type: "prasmanan",
    drop_off_location: "Pantry",
  };
  menuDetails.value = {
    heavy_meal: [],
    snack: [],
    beverages: [],
  };
  selectedInstitutionId.value = "";
};

// Fetch institutions if admin
onMounted(async () => {
  if (canSelectInstitution.value) {
    try {
      const response = await axios.get(`${API_URL}/api/institutions/`, {
        headers: { Authorization: `Bearer ${authStore.token}` },
      });
      institutions.value = response.data;
    } catch (error) {
      console.error("Failed to fetch institutions:", error);
    }
  }
});

const handleSubmit = async () => {
  if (!servingDate.value) {
    alert("Please select a Serving Date");
    return;
  }
  if (!authStore.userId) {
    alert("User ID not found. Please log in again.");
    return;
  }

  // Determine Institution ID
  let orderInstitutionId = authStore.institutionId;
  if (canSelectInstitution.value) {
    if (!selectedInstitutionId.value) {
      alert("Please select an Institution");
      return;
    }
    orderInstitutionId = selectedInstitutionId.value;
  }

  try {
    isSubmitting.value = true;

    // Construct Payload
    // Staff Allocation: Hardcoded 'all_guest' key as per requirement
    const finalStaffAllocation = {
      all_guest: {
        total: staffAllocation.value.total,
        serving_type: staffAllocation.value.serving_type,
        drop_off_location: staffAllocation.value.drop_off_location,
      },
    };

    // Calculate total portion based on staff allocation total
    // (Since there is only one entry 'all_guest', it is just that total)
    const totalPortion = staffAllocation.value.total;

    const payload = {
      order_date: servingDate.value,
      order_type: "SPECIAL",
      total_portion: totalPortion,
      staff_allocation: finalStaffAllocation,
      menu_details: menuDetails.value,
      dropping_location_food: droppingLocationFood.value,
      special_notes: "",
      institution_id: orderInstitutionId, 
    };

    // Query parameter created_by is required
    const params = new URLSearchParams();
    params.append("created_by", authStore.userId);

    await axios.post(`${API_URL}/api/orders/`, payload, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authStore.token}`,
      },
      params: params,
    });

    emit("order-created");
    emit("update:open", false);
    resetForm();
  } catch (error: any) {
    console.error("Failed to create order:", error);
    alert(
      `Failed to create order: ${error.response?.data?.detail || error.message}`,
    );
  } finally {
    isSubmitting.value = false;
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
      <!-- Header Area -->
      <div
        class="bg-zinc-50 border-b border-zinc-100 p-6 flex items-center justify-between shrink-0"
      >
        <div>
          <div class="flex items-center gap-3 mb-1">
            <h2 class="text-xl font-bold text-zinc-900">
              Create Special Order
            </h2>
            <Badge class="bg-indigo-100 text-indigo-700 border-indigo-200"
              >SPECIAL</Badge
            >
          </div>
          <p class="text-sm text-zinc-500">
            Create a new catering order for specific events.
          </p>
        </div>
      </div>

      <!-- Body - Scrollable -->
      <div
        class="p-6 space-y-6 overflow-y-auto"
        style="max-height: calc(85vh - 160px)"
      >
        <!-- Institution Selection (Admin Only) -->
        <div v-if="canSelectInstitution" class="space-y-2">
            <label class="text-xs font-bold text-zinc-500 uppercase tracking-widest">Assign Institution</label>
            <Select v-model="selectedInstitutionId">
                <SelectTrigger class="bg-white border-zinc-300 focus:ring-emerald-500">
                    <SelectValue placeholder="Select institution..." />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem 
                        v-for="inst in institutions" 
                        :key="inst.institution_id" 
                        :value="inst.institution_id"
                    >
                        {{ inst.name }}
                    </SelectItem>
                </SelectContent>
            </Select>
            <p class="text-[11px] text-zinc-500">Select the institution this order belongs to.</p>
        </div>

        <!-- Section 1: Basic Info -->
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <label
              class="text-xs font-bold text-zinc-500 uppercase tracking-widest"
              >Serving Date (H-Day)</label
            >
            <Input
              type="date"
              v-model="servingDate"
              class="bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
            />
          </div>
          <div class="space-y-2">
            <label
              class="text-xs font-bold text-zinc-500 uppercase tracking-widest"
              >Food Drop Location</label
            >
            <Input
              v-model="droppingLocationFood"
              placeholder="e.g. Meeting Room 1"
              class="bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
            />
          </div>
        </div>

        <!-- Section 2: Staff Allocation (Simplified) -->
        <div class="space-y-3 pt-2">
          <h3
            class="font-bold text-zinc-700 text-sm uppercase tracking-wide border-b pb-2"
          >
            Staff Allocation (All Guest)
          </h3>
          <div
            class="grid grid-cols-3 gap-4 bg-zinc-50 p-4 rounded-lg border border-zinc-100"
          >
            <div class="space-y-1">
              <label class="text-[10px] font-semibold text-zinc-500 uppercase"
                >Total Portions</label
              >
              <Input
                type="number"
                v-model.number="staffAllocation.total"
                class="bg-white"
              />
            </div>
            <div class="space-y-1">
              <label class="text-[10px] font-semibold text-zinc-500 uppercase"
                >Serving Type</label
              >
              <Input
                v-model="staffAllocation.serving_type"
                placeholder="e.g. prasmanan"
                class="bg-white"
              />
            </div>
            <div class="space-y-1">
              <label class="text-[10px] font-semibold text-zinc-500 uppercase"
                >Staff Drop-off Loc</label
              >
              <Input
                v-model="staffAllocation.drop_off_location"
                placeholder="e.g. Pantry"
                class="bg-white"
              />
            </div>
          </div>
        </div>

        <!-- Section 3: Menu Details -->
        <div class="space-y-6 pt-2">
          <div class="flex items-center justify-between border-b pb-2">
            <h3 class="font-bold text-zinc-700 text-sm uppercase tracking-wide">
              Menu Details
            </h3>
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
          <Button variant="ghost" @click="handleClose" :disabled="isSubmitting">
            Cancel
          </Button>

          <Button
            class="bg-emerald-600 hover:bg-emerald-700 text-white gap-2"
            :disabled="isSubmitting"
            @click="handleSubmit"
          >
            <CheckCircle2 class="h-4 w-4" />
            {{ isSubmitting ? "Creating..." : "Create Order" }}
          </Button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

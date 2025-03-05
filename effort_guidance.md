# 📌 Effort Estimation & Points Schema Documentation
## **For All Repositories & Projects in the `olemiss-fm` Organization**
**Author:** @sstubbs-olemiss  
**Last Updated:** *3/5/2025*  

---

## **1. Overview**
Effort estimation follows **Agile best practices** and the **Fibonacci sequence (1, 2, 3, 5, 8, etc.)** to provide **realistic capacity planning** for all tasks in `olemiss-fm` projects. This system ensures:

✔️ **Predictable workload distribution**  
✔️ **Clear expectations on task complexity**  
✔️ **Better sprint planning & deliverable tracking**  
✔️ **Consistent estimation across all projects and teams**  

This guidance applies to all repositories in the **Ole Miss `.github` organization**, including but not limited to:

- **`utility_billing`**
- **`utilities_automation_scripts`**
- **`APIFM`**
- **`slack_bot`**
- **`sqlserver`**
- **`landing_page`**
- **`documentation`**

---

## **2. Effort Point Definitions**
Each task is **assigned an effort score (1-5)** based on **complexity, dependencies, and execution time**.

| **Effort** | **Definition** | **Example Task** |
|------------|--------------|------------------|
| **1** | Small, quick task. No dependencies. <br> Requires minimal setup. | Minor config updates, modifying a single test case. |
| **2** | Slightly more effort than a `1`. <br> Might involve simple coding, minor infrastructure changes, or validation updates. | Updating test cases for new data types, modifying a small script, adding a basic API endpoint. |
| **3** | Moderate complexity. <br> Requires new code but no major dependencies. | Writing unit tests for specific functions, modifying CI/CD YAML files, implementing a new automation script. |
| **5** | High effort task. <br> Requires multiple changes or dependencies. | Setting up test databases, Jenkins pipeline modifications, modifying API authentication mechanisms, major code refactors. |
| **8+** | **Too large**—needs breaking down into smaller tasks. | Full-scale refactoring, major system rewrites, complex integrations. |

🚨 **Note:**  
- **No single task should exceed 5 points.**  
- Tasks estimated at **8 or more should be split** into smaller, manageable pieces.  

---

## **3. Examples of Task Breakdown**
Here’s how effort estimation is applied to different types of projects across Ole Miss FM IT:

### **✅ Example: Simple Task (Effort: 1)**
**Project:** `utility_billing`  
**Task:** Update GitHub Actions YAML to trigger on `dev` branch.  
- Requires modifying a YAML file.  
- No dependencies.  
- **Estimate: 1 point.**

**Project:** `APIFM`  
**Task:** Update an API endpoint to include a new field in response.  
- Requires modifying a FastAPI model and JSON schema.  
- No significant code dependencies.  
- **Estimate: 1 point.**

---

### **✅ Example: Moderate Task (Effort: 3)**
**Project:** `utilities_automation_scripts`  
**Task:** Implement unit tests for SAP Export.  
- Requires **new test cases** and **mock data setup**.  
- No significant system dependencies.  
- **Estimate: 3 points.**

**Project:** `sqlserver`  
**Task:** Modify Docker configuration for local database testing.  
- Requires modifying `Dockerfile` and `docker-compose.yml`.  
- No major infrastructure changes.  
- **Estimate: 3 points.**

---

### **✅ Example: Complex Task (Effort: 5)**
**Project:** `utility_billing`  
**Task:** Modify Jenkins Pipeline to Support `dev` Branch.  
- Requires **CI/CD reconfiguration**.  
- **Dependent on GitHub Actions changes & on-prem runner**.  
- **Estimate: 5 points.**

**Project:** `landing_page`  
**Task:** Implement a complete UI redesign.  
- Requires **modifying multiple React components**.  
- Affects **frontend, backend API interactions, and routing**.  
- **Estimate: 5 points.**

---

## **4. Effort Allocation & Capacity Planning**
### **Sprint Guidelines**
- Each **developer should not exceed ~10 points per sprint**.  
- **Avoid overloading critical path tasks** in a single sprint.  
- **Tasks should be completed incrementally**—don’t hold large efforts until the end.  

### **Example Developer Workload**
| Developer | Task | Effort |
|-----------|------|--------|
| Thomas | Modify Jenkins Pipeline | 5 |
| Thomas | Implement SAP Export Unit Tests | 3 |
| Thomas | Update GitHub Actions YAML | 1 |
| Thomas | Configure On-Prem Runner | 3 |
| **Total:** | **Sprint Allocation** | **10 Points** |

---

## **5. Expectations & Best Practices**
✅ **Effort is an estimate, not an exact measurement.**  
✅ **Devs should raise concerns if effort is underestimated.**  
✅ **No single task should exceed 5 points**—break down larger efforts.  
✅ **CI/CD and runtime validation must pass before merging code.**  
✅ **Use `dev` branch for testing before merging to `main`** (if applicable).  
✅ **Ensure all estimates are reviewed before sprint planning.**  

---

## **6. Next Steps**
1️⃣ **Developers to review effort estimates for clarity.**  
2️⃣ **Ensure GitHub issues have appropriate effort assignments.**  
3️⃣ **Monitor sprint velocity and adjust estimates if needed.**  

---

## **7. Conclusion**
This effort estimation system ensures **consistent task sizing, predictable workloads, and structured sprint planning** across **all Ole Miss FM IT projects**. 

By keeping effort estimates aligned, we can **optimize our development workflow, improve CI/CD stability, and ensure high-quality deployments**. 🚀  

---

### **🔹 Questions? Discuss in DevOps Slack.**
🚀 **Let's keep our estimates lean and execution predictable!**  
